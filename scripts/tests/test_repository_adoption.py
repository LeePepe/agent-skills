"""Catalog contract behavior through the real approved provider audit CLI."""
import json
import unittest

from adoption_fixture import CatalogFixture, PIN, ProviderFixture, git, workflow


class RepositoryAdoptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provider = ProviderFixture()
        cls.addClassCleanup(cls.provider.close)

    def setUp(self):
        self.repo = CatalogFixture()
        self.addCleanup(self.repo.close)

    def test_tracked_catalog_satisfies_native_published_audit(self):
        result = self.repo.context(self.provider.root, "audit")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def rejected_edit(self, path, edit, expected):
        original = (self.repo.root / path).read_text()
        self.repo.write(path, edit(original))
        result = self.repo.context(self.provider.root, "audit")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(expected, result.stderr)
        self.repo.write(path, original)

    def test_metadata_invalidity_never_falls_back_to_valid_directory(self):
        for edit in (lambda _: "{}", lambda s: s.replace('"schema": 1', '"schema": true'),
                     lambda s: s.replace('"schema": 1', '"schema": 1, "schema": 1'),
                     lambda s: s.replace(PIN, "main")):
            with self.subTest(edit=edit):
                self.rejected_edit(".github/repo-contract.json", edit, "invalid repository metadata")

    def test_pin_and_reviewer_route_parity(self):
        self.rejected_edit(".github/workflows/ci.yml", lambda s: s.replace(PIN, "1" * 40),
                           "mixed shared-ci pins")
        self.rejected_edit("AGENTS.md", lambda s: s.replace(PIN, "1" * 40),
                           "versioned protocol route differs")
        self.rejected_edit(".github/workflows/review.yml",
                           lambda s: s.replace("rules-file: docs/repository-gates.md", "rules-file: AGENTS.md"),
                           "rules-file to the repository guide")

    def test_directory_routes_and_complete_required_sections(self):
        for target in ("missing.md", "docs/repository-gates.md#missing", "../README.md"):
            self.rejected_edit("AGENTS.md", lambda s: s + f"\n- Read: [Missing]({target})\n",
                               "contract_agents")
        self.rejected_edit("AGENTS.md", lambda s: s + "\nRun scripts/verify now.\n", "index-only")
        for section in ("Protocol", "Verify", "Required checks", "Red lines", "Delivery"):
            with self.subTest(section=section):
                self.rejected_edit("docs/repository-gates.md",
                                   lambda s: s.replace("## " + section, "## Other " + section),
                                   "guide is missing section")

    def test_symlink_guide_is_not_admitted(self):
        guide = self.repo.root / "docs/repository-gates.md"
        guide.unlink()
        guide.symlink_to("../README.md")
        result = self.repo.context(self.provider.root, "audit")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("without symlinks", result.stderr)

    def test_missing_or_ownerless_protection_is_rejected(self):
        self.rejected_edit(".github/CODEOWNERS",
                           lambda s: s.replace("/docs/repository-gates.md", "/unused-guide.md"),
                           "CODEOWNERS does not cover")
        for path in ("/AGENTS.md", "/.github/repo-contract.json", "/docs/repository-gates.md"):
            self.rejected_edit(".github/CODEOWNERS", lambda s: s + "\n" + path + "\n",
                               "leaves protected document unowned")

    def test_recipe_test_ownership_is_exclusive_even_outside_skills(self):
        paths = ("scripts/tests/test_consumer_authority.py", "scripts/tests/test_dispatch_safety.py",
                 "scripts/tests/test_entrypoint_recipe.py", "scripts/tests/test_layer_routing_recipe.py")
        for path in paths:
            result = self.repo.context(self.provider.root, "resolve", path, "--format", "layer")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "Catalog")
        self.repo.write(paths[0], "# ownership-only fixture; no recipe executed\n")
        git(self.repo.root, "add", paths[0])
        self.rejected_edit("scripts/tech-context.md",
                           lambda s: s.replace("owns: [", "owns: [scripts/tests/**, "), "overlap")
        self.repo.write("scripts/unowned.py", "pass\n")
        git(self.repo.root, "add", "scripts/unowned.py")
        result = self.repo.context(self.provider.root, "audit")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unmapped_path", result.stderr)

    def test_native_ci_steps_and_full_quality_caller_are_preserved(self):
        native = workflow(self.provider.root, (self.repo.root / ".github/workflows/validate-skills.yml").read_text())
        job = native["jobs"]["validate"]
        self.assertEqual(job["runs-on"], "ubuntu-latest")
        self.assertEqual(job["steps"][:4], [
            {"uses": "actions/checkout@v4"},
            {"uses": "actions/setup-python@v5", "with": {"python-version": "3.12"}},
            {"name": "Validate SKILL.md frontmatter + links", "run": "python3 scripts/validate_skills.py"},
            {"name": "Check registry / plugin.json / README in sync", "run": "python3 scripts/gen_registry.py --check"},
        ])
        ci = workflow(self.provider.root, (self.repo.root / ".github/workflows/ci.yml").read_text())
        quality = ci["jobs"]["quality"]
        self.assertTrue(quality["uses"].endswith("quality.yml@" + PIN))
        self.assertEqual(quality["with"]["verify-command"], "scripts/verify --all")
        self.assertEqual(quality["with"]["changed-only"], False)
        self.assertNotIn("test-integrity", quality["with"])

    def test_entire_guide_contains_current_protocol_and_resolves_provider_link(self):
        guide = (self.repo.root / "docs/repository-gates.md").read_bytes()
        self.assertLessEqual(len(guide), 24000)
        protocol = (self.provider.root / "ai/agent-protocol.md").read_text()
        prefix = "https://github.com/LeePepe/shared-ci/blob/" + PIN + "/ai/"
        expected = protocol.replace("(repo-contract.md#", "(" + prefix + "repo-contract.md#")
        self.assertTrue(guide.endswith(expected.encode()), "complete selected policy must be retained")
        contract = (self.provider.root / "ai/repo-contract.md").read_text()
        self.assertIn("## Repository development contract", contract)
        self.assertIn("**Draft/setup-held**", guide.decode())
        self.assertEqual(json.loads((self.repo.root / ".github/repo-contract.json").read_text())["shared_ci"], PIN)


if __name__ == "__main__":
    unittest.main()

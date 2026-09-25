"""Existing catalog tools exercised through their public CLI on isolated copies."""
import json
import py_compile
import subprocess
import sys
import unittest

from adoption_fixture import CatalogFixture, ProviderFixture, environment, git, run


class NativeToolingTests(unittest.TestCase):
    def setUp(self):
        self.repo = CatalogFixture()
        self.addCleanup(self.repo.close)

    def tool(self, name, *args):
        return run(self.repo.root, sys.executable, "-B", "scripts/" + name, *args, check=False)

    def test_all_seventeen_skills_and_generated_catalog_remain_valid(self):
        result = self.tool("validate_skills.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("17 个 SKILL.md", result.stdout)
        self.assertEqual(self.tool("gen_registry.py", "--check").returncode, 0)
        self.assertEqual(json.loads((self.repo.root / "skills.json").read_text())["count"], 17)

    def test_validator_rejects_empty_name_description_and_broken_links(self):
        target = self.repo.root / "skills/repo/code-review/SKILL.md"
        valid = "---\nname: code-review\ndescription: valid\nuser-invocable: true\n---\n"
        for content in ("# no frontmatter\n", valid.replace("name: code-review", "name:"),
                        valid.replace("description: valid", "description:"),
                        valid.replace("code-review", "wrong-name"),
                        valid + "[missing](missing.md)\n"):
            with self.subTest(content=content):
                target.write_text(content)
                result = self.tool("validate_skills.py")
                self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_check_reports_drift_without_mutation_then_generation_repairs_fixture(self):
        registry = self.repo.root / "skills.json"
        registry.write_text("{}\n")
        result = self.tool("gen_registry.py", "--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("skills.json", result.stdout)
        self.assertEqual(registry.read_text(), "{}\n")
        self.assertEqual(self.tool("gen_registry.py").returncode, 0)
        self.assertEqual(self.tool("gen_registry.py", "--check").returncode, 0)
        self.assertEqual(json.loads(registry.read_text())["count"], 17)

    def test_generator_preserves_invocation_metadata_and_surrounding_readme(self):
        target = self.repo.root / "skills/repo/code-review/SKILL.md"
        target.write_text("---\nname: code-review\ndescription: '中文 fixture'\nuser-invocable: true\n---\n")
        readme = self.repo.root / "README.md"
        readme.write_text("fixture intro\n" + readme.read_text() + "\nfixture outro\n")
        result = self.tool("gen_registry.py")
        self.assertEqual(result.returncode, 0, result.stdout)
        data = json.loads((self.repo.root / "skills.json").read_text())
        item = next(s for s in data["skills"] if s["name"] == "code-review")
        self.assertTrue(item["user_invocable"])
        self.assertEqual(item["description"], "中文 fixture")
        self.assertEqual(item["path"], "skills/repo/code-review")
        self.assertTrue(readme.read_text().startswith("fixture intro\n"))
        self.assertTrue(readme.read_text().endswith("fixture outro\n"))
        before = readme.read_bytes()
        self.assertEqual(self.tool("gen_registry.py").returncode, 0)
        self.assertEqual(readme.read_bytes(), before)

    def test_syntax_parses_bundled_scripts_without_executing_them(self):
        marker = self.repo.root / "must-not-exist"
        self.repo.write("scripts/install-symlinks.sh", "#!/usr/bin/env bash\ntouch must-not-exist\n")
        self.assertEqual(self.tool("check_syntax.py").returncode, 0)
        self.assertFalse(marker.exists())
        self.repo.write("scripts/install-symlinks.sh", "#!/usr/bin/env bash\nif then\n")
        self.assertNotEqual(self.tool("check_syntax.py").returncode, 0)
        self.repo.write("scripts/install-symlinks.sh", "#!/usr/bin/env bash\nexit 0\n")
        self.repo.write("scripts/validate_skills.py", "def invalid(:\n")
        self.assertNotEqual(self.tool("check_syntax.py").returncode, 0)

    def test_empty_or_skipped_owned_test_selection_is_not_success(self):
        paths = sorted(str(p.relative_to(self.repo.root))
                       for p in (self.repo.root / "scripts/tests").glob("test_*.py"))
        git(self.repo.root, "rm", "--", *paths)  # staged fixture deletion, not missing indexed files
        result = self.tool("run_tests.py", "Tooling")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no tests selected", result.stderr)
        relative = "scripts/tests/test_git_hook_isolation.py"
        self.repo.write(relative, "import unittest\n"
                        "class Example(unittest.TestCase):\n"
                        "    @unittest.skip('fixture skip must fail verification')\n"
                        "    def test_case(self):\n        self.assertTrue(True)\n")
        git(self.repo.root, "add", "--", relative)
        result = self.tool("run_tests.py", "Tooling")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("selected tests skipped", result.stderr)


class TestSelectionAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.repo = CatalogFixture()
        self.addCleanup(self.repo.close)
        # A small, genuinely tracked/staged and Tooling-owned suite keeps these
        # runner-boundary fixtures nonrecursive without weakening their admission.
        paths = sorted(str(p.relative_to(self.repo.root))
                       for p in (self.repo.root / "scripts/tests").glob("test_*.py"))
        git(self.repo.root, "rm", "--", *paths)
        self.admitted = "scripts/tests/test_git_hook_isolation.py"
        self.repo.write(self.admitted, self.module("admitted-imported"))
        git(self.repo.root, "add", "--", self.admitted)

    @staticmethod
    def module(marker):
        return ("from pathlib import Path\nimport unittest\n"
                f"Path({marker!r}).write_text('module executed')\n"
                "class Admitted(unittest.TestCase):\n"
                "    def test_admitted(self): self.assertEqual(2 + 2, 4)\n")

    def runner(self, selector="Tooling", *, python_args=()):
        return run(self.repo.root, sys.executable, "-B", *python_args,
                   "scripts/run_tests.py", selector, check=False)

    def rejected(self, relative, selector="Tooling"):
        result = self.runner(selector)
        self.assertFalse((self.repo.root / "unexpected-imported").exists(), result.stdout + result.stderr)
        self.assertFalse((self.repo.root / "admitted-imported").exists(), "admit all before importing any")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("test admission", result.stderr)
        self.assertIn(relative, result.stderr)

    def test_ignored_unowned_module_is_rejected_before_import(self):
        relative = "scripts/tests/test_review_probe_unowned.py"
        self.repo.write(relative, self.module("unexpected-imported"))
        (self.repo.root / ".git/info/exclude").write_text(relative + "\n")
        self.assertEqual(git(self.repo.root, "ls-files", "--", relative), "")
        self.rejected(relative)

    def test_untracked_and_tracked_unmapped_candidates_never_execute(self):
        relative = "scripts/tests/test_unowned.py"
        self.repo.write(relative, self.module("unexpected-imported"))
        self.rejected(relative)
        git(self.repo.root, "add", "--", relative)
        provider = ProviderFixture()
        self.addCleanup(provider.close)
        resolved = self.repo.context(provider.root, "resolve", relative, "--format", "layer")
        self.assertNotEqual(resolved.returncode, 0)
        self.assertIn("unmapped", resolved.stderr)
        self.rejected(relative)

    def test_future_mapped_but_unstaged_recipe_is_not_imported_by_either_selector(self):
        relative = "scripts/tests/test_consumer_authority.py"
        self.repo.write(relative, self.module("unexpected-imported"))
        for selector in ("Tooling", "Catalog"):
            self.rejected(relative, selector)

    def test_exact_discovery_seam_must_be_tracked_before_it_executes(self):
        relative = "skills/repo/code-review/scripts/test_discover_review_context.py"
        git(self.repo.root, "rm", "--cached", "--", relative)
        self.repo.write(relative, self.module("unexpected-imported"))
        for ignored in (False, True):
            if ignored:
                (self.repo.root / ".git/info/exclude").write_text(relative + "\n")
            self.rejected(relative, "Catalog")

    def test_nested_package_initializers_and_test_modules_never_autodiscover(self):
        for directory in ("scripts/tests", "skills/repo/code-review/scripts"):
            with self.subTest(directory=directory):
                package = directory + "/nested"
                self.repo.write(package + "/__init__.py", self.module("unexpected-imported"))
                self.repo.write(package + "/test_git_hook_isolation.py", self.module("unexpected-imported"))
                for selector in ("Catalog", "Tooling"):
                    self.rejected(package, selector)
                (self.repo.root / package / "__init__.py").unlink()
                self.rejected(package)
                (self.repo.root / package / "test_git_hook_isolation.py").unlink()

    def test_module_and_directory_symlinks_never_execute(self):
        selected = self.repo.root / self.admitted
        self.repo.write("payload.py", self.module("unexpected-imported"))
        selected.unlink()
        selected.symlink_to(self.repo.root / "payload.py")
        self.rejected(self.admitted)
        git(self.repo.root, "add", "--", self.admitted)
        self.rejected(self.admitted)
        selected.unlink()
        self.repo.write(self.admitted, self.module("unexpected-imported"))
        git(self.repo.root, "add", "--", self.admitted)
        directory = self.repo.root / "scripts/tests"
        saved = self.repo.root / "saved-tests"
        directory.rename(saved)
        directory.symlink_to(saved, target_is_directory=True)
        self.rejected("scripts/tests")

    def test_unmerged_and_flagged_index_entries_are_rejected_without_import(self):
        for flag in ("assume-unchanged", "skip-worktree"):
            git(self.repo.root, "update-index", "--" + flag, self.admitted)
            before = (self.repo.root / ".git/index").read_bytes()
            self.rejected(self.admitted)
            self.assertEqual((self.repo.root / ".git/index").read_bytes(), before)
            git(self.repo.root, "update-index", "--no-" + flag, self.admitted)
        blob = git(self.repo.root, "rev-parse", "HEAD:" + self.admitted)
        rows = f"0 {'0' * 40}\t{self.admitted}\n" + "".join(
            f"100644 {blob} {stage}\t{self.admitted}\n" for stage in (1, 2, 3))
        subprocess.run(["git", "update-index", "--index-info"], cwd=self.repo.root,
                       env=environment(), input=rows, text=True, check=True, capture_output=True)
        self.rejected(self.admitted)

    def test_intent_to_add_does_not_count_as_staged_admission(self):
        relative = "scripts/tests/test_consumer_authority.py"
        self.repo.write(relative, self.module("unexpected-imported"))
        git(self.repo.root, "add", "-N", "--", relative)
        self.rejected(relative, "Catalog")
        result = self.runner("Catalog")
        self.assertIn("intent-to-add", result.stderr)

    def test_unreadable_candidate_directory_fails_before_loading_any_tests(self):
        relative = "scripts/tests/unreadable"
        self.repo.write(relative + "/test_hidden.py", self.module("unexpected-imported"))
        directory = self.repo.root / relative
        directory.chmod(0)
        try:
            self.rejected(relative)
        finally:
            directory.chmod(0o755)

    def test_admitted_import_assertion_and_load_tests_errors_reach_their_real_routes(self):
        prefix = "from pathlib import Path\nPath('admitted-imported').write_text('executed')\n"
        cases = (
            ("import missing_admission_fixture_module\n", "ModuleNotFoundError"),
            ("import unittest\nclass Broken(unittest.TestCase):\n"
             "    def test_assertion(self): self.assertEqual(1, 2)\n", "AssertionError"),
            ("def load_tests(*args): raise RuntimeError('admitted load_tests error')\n", "admitted load_tests error"),
            ("# empty but admitted module\n", "no tests selected"),
        )
        for content, expected in cases:
            with self.subTest(expected=expected):
                self.repo.write(self.admitted, prefix + content)
                git(self.repo.root, "add", "--", self.admitted)
                result = self.runner()
                self.assertTrue((self.repo.root / "admitted-imported").exists())
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("test admission failed", result.stderr)
                self.assertIn(expected, result.stderr)
                (self.repo.root / "admitted-imported").unlink()

    def test_staged_declared_suites_execute_and_preserve_all_four_future_recipe_seams(self):
        provider = ProviderFixture()
        self.addCleanup(provider.close)
        for layer in ("Tooling", "Catalog"):
            result = self.repo.context(provider.root, "field", layer, "scope")
            self.assertEqual(result.returncode, 0, result.stderr)
            paths = [p for p in json.loads(result.stdout) if p.startswith("scripts/tests/test_")]
            if layer == "Catalog":
                self.assertEqual(set(paths), {"scripts/tests/test_consumer_authority.py",
                                             "scripts/tests/test_dispatch_safety.py",
                                             "scripts/tests/test_entrypoint_recipe.py",
                                             "scripts/tests/test_layer_routing_recipe.py"})
                paths.append("skills/repo/code-review/scripts/test_discover_review_context.py")
            for number, path in enumerate(paths):
                owner = self.repo.context(provider.root, "resolve", path, "--format", "layer")
                self.assertEqual(owner.returncode, 0, owner.stderr)
                self.assertEqual(owner.stdout.strip(), layer)
                self.repo.write(path, self.module(layer + "-" + str(number)))
                git(self.repo.root, "add", "--", path)
            result = self.runner(layer)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for number, _ in enumerate(paths):
                self.assertTrue((self.repo.root / (layer + "-" + str(number))).exists())

    def test_current_admitted_source_executes_instead_of_ignored_bytecode(self):
        source = self.repo.root / self.admitted
        payload = self.repo.root / "cache-payload.py"
        payload.write_text(self.module("unexpected-imported"))
        # Apple Python may default its cache prefix outside this disposable
        # repository. Use the same fixture-local path for creation and reading.
        cache_root = self.repo.root / "bytecode-cache"
        python_args = ("-X", "pycache_prefix=" + str(cache_root))
        cache = run(self.repo.root, sys.executable, "-B", *python_args, "-c",
                    "import importlib.util, sys; print(importlib.util.cache_from_source(sys.argv[1]))",
                    str(source)).stdout.strip()
        self.assertTrue(cache.startswith(str(cache_root) + "/"))
        py_compile.compile(str(payload), cfile=cache, dfile=str(source), doraise=True,
                           invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
        self.assertTrue(git(self.repo.root, "check-ignore", "--", cache))
        self.repo.write("scripts/tests/local-notes.md", "unrelated non-executable notes are not test candidates\n")
        result = self.runner(python_args=python_args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.repo.root / "admitted-imported").exists())
        self.assertFalse((self.repo.root / "unexpected-imported").exists())

    def test_unsupported_selectors_fail_before_import(self):
        for args in ((), ("unknown",), ("",), ("Tooling", "extra")):
            result = run(self.repo.root, sys.executable, "-B", "scripts/run_tests.py", *args, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("usage:", result.stderr)
            self.assertFalse((self.repo.root / "admitted-imported").exists())


if __name__ == "__main__":
    unittest.main()

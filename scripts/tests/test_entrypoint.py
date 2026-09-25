"""Caller-pin/route checks and a concrete repo-kit init output, without dispatch."""
import importlib.util
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("entrypoint", ROOT / "scripts/check_entrypoint.py")
entrypoint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entrypoint)
PIN = "761fe6b0b3ca5e2c57d244182d495ab8041851fa"


class EntrypointTests(unittest.TestCase):
    def setUp(self):
        local_names = subprocess.check_output(["git", "rev-parse", "--local-env-vars"], text=True).splitlines()
        self.env = {key: value for key, value in os.environ.items() if key not in local_names}
        self.scratch = tempfile.TemporaryDirectory(prefix="entrypoint-")
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.git("init", "-q")
        self.caller = self.root / ".github/workflows/ci.yml"
        self.caller.parent.mkdir(parents=True)
        self.caller.write_text(f"jobs:\n  quality:\n    uses: LeePepe/shared-ci/.github/workflows/quality.yml@{PIN}\n")
        self.git("add", ".github/workflows/ci.yml")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, env=self.env,
                              check=True, text=True, capture_output=True)

    def route(self, target):
        return (f"[protocol](https://github.com/LeePepe/shared-ci/blob/{PIN}/ai/agent-protocol.md)"
                f"\n[local]({target})")

    def test_local_only_file_is_not_a_valid_route(self):
        (self.root / "local.md").write_text("# Local only\n")
        with self.assertRaisesRegex(ValueError, "tracked"):
            entrypoint.validate_routes(self.root, self.route("local.md"), PIN)

    def test_named_fragments_must_exist_outside_code_fences(self):
        (self.root / "guide.md").write_text("# Real heading\n```md\n## Fenced heading\n```\n## Real heading\n")
        self.git("add", "guide.md")
        for fragment in ("real-heading", "real-heading-1"):
            self.assertEqual(entrypoint.validate_routes(self.root, self.route(f"guide.md#{fragment}"), PIN), 2)
        for fragment in ("absent", "fenced-heading"):
            with self.subTest(fragment=fragment), self.assertRaisesRegex(ValueError, "fragment"):
                entrypoint.validate_routes(self.root, self.route(f"guide.md#{fragment}"), PIN)

    def test_bootstrap_pin_does_not_require_agents_prose(self):
        self.assertFalse((self.root / "AGENTS.md").exists())
        self.assertEqual(entrypoint.shared_ci_pin(self.root), PIN)

    def test_branch_ref_cannot_bootstrap(self):
        self.caller.write_text(self.caller.read_text().replace(PIN, "main"))
        with self.assertRaisesRegex(ValueError, "full-SHA"):
            entrypoint.shared_ci_pin(self.root)

    def test_mixed_callers_fail(self):
        (self.caller.parent / "review.yml").write_text(
            "jobs:\n  review:\n    uses: LeePepe/shared-ci/.github/workflows/codex-review.yml@" + "a" * 40 + "\n")
        self.git("add", ".github/workflows/review.yml")
        with self.assertRaisesRegex(ValueError, "revisions differ"):
            entrypoint.shared_ci_pin(self.root)

    def test_protocol_and_provider_docs_must_match_manifest_pin(self):
        protocol = f"[protocol](https://github.com/LeePepe/shared-ci/blob/{PIN}/ai/agent-protocol.md)"
        self.assertEqual(entrypoint.validate_routes(self.root, protocol, PIN), 1)
        with self.assertRaisesRegex(ValueError, "exact protocol"):
            entrypoint.validate_routes(self.root, protocol.replace(PIN, "a" * 40), PIN)
        with self.assertRaisesRegex(ValueError, "documentation revision"):
            entrypoint.validate_routes(self.root, protocol + "\n[docs](https://github.com/LeePepe/shared-ci/tree/main/ai)", PIN)

    def test_missing_or_escaping_route_fails(self):
        protocol = f"[protocol](https://github.com/LeePepe/shared-ci/blob/{PIN}/ai/agent-protocol.md)"
        for target in ("missing.md", "../outside.md"):
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, "route"):
                entrypoint.validate_routes(self.root, protocol + f"\n[local]({target})", PIN)

    def test_repo_kit_init_example_is_a_resolvable_link_index(self):
        reference = (ROOT / "skills/repo/repo-kit/references/entrypoint.md").read_text()
        example = re.search(r"```markdown\n(.*?)```", reference, re.S).group(1)
        (self.root / "AGENTS.md").write_text(example)
        for target in entrypoint.LINK.findall(example):
            if "://" not in target:
                path = self.root / target
                path.parent.mkdir(parents=True, exist_ok=True)
                if path != self.caller:
                    path.write_text("# Maintained authority\n")
        self.git("add", ".")
        self.assertEqual(entrypoint.shared_ci_pin(self.root), PIN)
        self.assertEqual(entrypoint.validate_routes(self.root, example, PIN), 9)
        self.assertTrue(all(line.startswith("- ") and entrypoint.LINK.search(line)
                            for line in example.splitlines()[1:] if line.strip() and not line.startswith("## ")))

    def test_symlink_unreadable_and_nonregular_routes_fail(self):
        guide = self.root / "guide.md"
        guide.write_text("# Guide\n")
        (self.root / "alias.md").symlink_to(guide)
        self.git("add", "guide.md", "alias.md")
        with self.assertRaisesRegex(ValueError, "symlink"):
            entrypoint.validate_routes(self.root, self.route("alias.md"), PIN)
        guide.chmod(0)
        try:
            with self.assertRaisesRegex(ValueError, "readable"):
                entrypoint.validate_routes(self.root, self.route("guide.md"), PIN)
        finally:
            guide.chmod(0o644)
        guide.unlink()
        guide.mkdir()
        with self.assertRaisesRegex(ValueError, "regular file"):
            entrypoint.validate_routes(self.root, self.route("guide.md"), PIN)

    def test_directory_routes_are_explicit_and_have_tracked_contents(self):
        folder = self.root / "guides"
        folder.mkdir()
        (folder / "one.md").write_text("# One\n")
        with self.assertRaisesRegex(ValueError, "tracked"):
            entrypoint.validate_routes(self.root, self.route("guides/"), PIN)
        self.git("add", "guides/one.md")
        self.assertEqual(entrypoint.validate_routes(self.root, self.route("guides/"), PIN), 2)
        for target in ("guides", "guides/#one"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                entrypoint.validate_routes(self.root, self.route(target), PIN)

    def test_fragment_only_and_percent_encoded_routes(self):
        content = self.route("#read-first") + "\n## Read first\n"
        (self.root / "AGENTS.md").write_text(content)
        (self.root / "two words.md").write_text("# 中文\n")
        self.git("add", "AGENTS.md", "two words.md")
        self.assertEqual(entrypoint.validate_routes(self.root, content, PIN), 2)
        self.assertEqual(entrypoint.validate_routes(self.root, self.route("two%20words.md#%E4%B8%AD%E6%96%87"), PIN), 2)
        for target in ("two%20words.md#missing", "%2e%2e/outside.md", "two%GGwords.md",
                       "guide.md?raw=1", "file:guide.md", "//example.invalid/guide.md"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                entrypoint.validate_routes(self.root, self.route(target), PIN)

    def test_cli_does_not_read_an_inherited_foreign_index(self):
        other = self.root / "other"
        other.mkdir()
        subprocess.run(["git", "init", "-q", str(other)], check=True, env=self.env)
        environment = {**self.env, "GIT_DIR": str(other / ".git"), "GIT_WORK_TREE": str(other),
                       "GIT_INDEX_FILE": str(other / ".git/index")}
        result = subprocess.run(["python3", str(ROOT / "scripts/check_entrypoint.py"),
                                 "--root", str(self.root), "--pin"], env=environment, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), PIN)

    def test_unsupported_link_and_heading_forms_are_not_silently_accepted(self):
        (self.root / "guide.md").write_text("# Rich [heading](elsewhere.md)\n<a id=\"custom\"></a>\n")
        self.git("add", "guide.md")
        for text in (self.route("guide.md") + "\n[local][reference]",
                     self.route("guide.md") + "\n<https://example.invalid>",
                     self.route("guide.md#rich-heading"), self.route("guide.md#custom")):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "unsupported"):
                entrypoint.validate_routes(self.root, text, PIN)

    def test_ordinary_tests_unowned_but_gate_and_permission_paths_protected(self):
        # Evaluate each pattern with Git's matcher, then apply CODEOWNERS'
        # last-match rule. Gitignore negation is not equivalent to an empty-owner
        # entry: an ignored parent prevents traversal into a re-included child.
        patterns = []
        for line in (ROOT / ".github/CODEOWNERS").read_text().splitlines():
            fields = line.split()
            if fields and not fields[0].startswith("#"):
                patterns.append((fields[0], len(fields) > 1))
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, env=self.env)
        cases = {"scripts/tests/test_example.py": False,
                 "skills/workflow/multica-delivery-supervisor/tests/recovery-cases.json": False,
                 "scripts/verify": True, "scripts/check_entrypoint.py": True,
                 "scripts/check_syntax.py": True, "scripts/validate_skills.py": True,
                 "scripts/gen_registry.py": True, "scripts/install-symlinks.sh": True,
                 ".githooks/pre-push": True, "docs/repository-gates.md": True,
                 ".github/workflows/ci.yml": True, ".github/workflows/review.yml": True,
                 "policy/main-protection.proposed.json": True}
        tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT, env=self.env).decode().split("\0")
        for path in filter(None, tracked):
            parts = Path(path).parts
            if "tests" in (part.lower() for part in parts) or Path(path).name.startswith("test_"):
                cases[path] = False
        for path, protected in cases.items():
            with self.subTest(path=path):
                observed = False
                for pattern, owned in patterns:
                    (self.root / ".gitignore").write_text(pattern + "\n")
                    result = subprocess.run(["git", "check-ignore", "--no-index", "-q", path], cwd=self.root, env=self.env)
                    self.assertIn(result.returncode, (0, 1))
                    if result.returncode == 0:
                        observed = owned
                self.assertEqual(observed, protected)


if __name__ == "__main__":
    unittest.main()

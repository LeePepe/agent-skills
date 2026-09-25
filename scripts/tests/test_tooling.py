"""Existing catalog tools exercised through their public CLI on isolated copies."""
import json
import sys
import unittest

from adoption_fixture import CatalogFixture, run


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
        for path in (self.repo.root / "scripts/tests").glob("test_*.py"):
            path.unlink()  # only this disposable fixture's copied test modules
        result = self.tool("run_tests.py", "Tooling")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no tests selected", result.stderr)
        self.repo.write("scripts/tests/test_only.py", "import unittest\n"
                        "class Example(unittest.TestCase):\n"
                        "    @unittest.skip('fixture skip must fail verification')\n"
                        "    def test_case(self):\n        self.assertTrue(True)\n")
        result = self.tool("run_tests.py", "Tooling")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("selected tests skipped", result.stderr)


if __name__ == "__main__":
    unittest.main()

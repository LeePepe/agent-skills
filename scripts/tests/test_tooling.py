"""Exercise the existing validators/generator with isolated, discriminating fixtures."""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load("validate_skills")
registry = load("gen_registry")


class ValidatorTests(unittest.TestCase):
    def validate(self, text):
        with tempfile.TemporaryDirectory(prefix="skill-validator-") as directory:
            root = Path(directory)
            skill = root / "skills/repo/sample"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(text)
            with patch.object(validator, "ROOT", root), patch.object(validator, "SKILLS_DIR", root / "skills"):
                with contextlib.redirect_stdout(io.StringIO()):
                    return validator.main()

    def test_valid_frontmatter(self):
        self.assertEqual(self.validate("---\nname: sample\ndescription: Use for samples.\n---\n"), 0)

    def test_empty_value_does_not_consume_next_line(self):
        self.assertEqual(validator.scalar("description:\nname: sample", "description"), "")
        self.assertEqual(self.validate("---\nname: sample\ndescription:\nuser-invocable: true\n---\n"), 1)

    def test_missing_frontmatter(self):
        self.assertEqual(self.validate("# sample\n"), 1)

    def test_wrong_name_and_oversized_description(self):
        self.assertEqual(self.validate("---\nname: wrong-name\ndescription: text\n---\n"), 1)
        self.assertEqual(self.validate("---\nname: sample\ndescription: " + "x" * 1025 + "\n---\n"), 1)

    def test_broken_reference_is_not_silently_accepted(self):
        self.assertEqual(self.validate("---\nname: sample\ndescription: text\n---\n[ref](missing.md)"), 1)

    def test_remote_links_are_not_local_paths(self):
        self.assertEqual(validator.local_md_links("[remote](https://example.invalid/a.md) [local](a.md)"), ["a.md"])


class RegistryTests(unittest.TestCase):
    def test_frontmatter_preserves_invocation_metadata(self):
        data = registry.parse_frontmatter("---\nname: sample\ndescription: '中文 text'\nuser-invocable: true\n---\n")
        self.assertEqual(data, {"name": "sample", "description": "中文 text", "user-invocable": "true"})

    def test_empty_description_does_not_become_invocation_flag(self):
        data = registry.parse_frontmatter("---\nname: sample\ndescription:\nuser-invocable: true\n---\n")
        self.assertNotIn("description", data)
        self.assertEqual(data["user-invocable"], "true")

    def test_generation_is_stable_and_preserves_surrounding_readme(self):
        skills = [{"name": "sample", "description": "中文 text", "category": "repo", "path": "skills/repo/sample"}]
        table = registry.render_readme_table(skills)
        readme = "intro\n<!-- SKILLS:BEGIN -->\nstale\n<!-- SKILLS:END -->\noutro\n"
        result = registry.splice_readme(readme, table)
        self.assertTrue(result.startswith("intro\n"))
        self.assertTrue(result.endswith("\noutro\n"))
        self.assertEqual(registry.splice_readme(result, table), result)
        self.assertEqual(json.loads(registry.render_registry(skills))["skills"], skills)
        self.assertEqual(json.loads(registry.render_plugin_json(skills[0]))["description"], "中文 text")


if __name__ == "__main__":
    unittest.main()

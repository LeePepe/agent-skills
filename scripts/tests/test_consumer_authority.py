"""Regression checks for skills migrated out of agent-skills.

The repo-kit recipe-text cases were removed with that skill. Check that all
migrated skills stay out of this repository's skill tree and catalog entries.
Run with: python3 -m unittest discover -s scripts/tests -v
"""
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MOVED_SKILLS = {
    "code-review": "skills/repo/code-review",
    "xcode-cli": "skills/repo/xcode-cli",
    "deep-research": "skills/research/deep-research",
    "auto-review-merge": "skills/repo/auto-review-merge",
    "my-designer": "skills/design/my-designer",
    "save-tool": "skills/meta/save-tool",
    "visual-design-modernization": "skills/design/visual-design-modernization",
    "layered-data-warehouse": "skills/repo/layered-data-warehouse",
    "repo-kit": "skills/repo/repo-kit",
    "shared-release": "skills/workflow/shared-release",
}


class MigratedSkillsTests(unittest.TestCase):
    def test_moved_skills_are_absent_from_tree_and_catalogs(self):
        catalog_names = {}
        for filename, key in (
            ("skills.json", "skills"),
            (".claude-plugin/marketplace.json", "plugins"),
        ):
            catalog = json.loads(ROOT.joinpath(filename).read_text(encoding="utf-8"))
            catalog_names[filename] = {entry["name"] for entry in catalog[key]}

        for name, path in MOVED_SKILLS.items():
            with self.subTest(skill=name, location="skills/"):
                self.assertFalse(ROOT.joinpath(path).exists(), path)
            for filename, names in catalog_names.items():
                with self.subTest(skill=name, location=filename):
                    self.assertNotIn(name, names)

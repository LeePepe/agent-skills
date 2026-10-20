"""Apply the repo's frontmatter/link rules to the seven nested role skills.

The root validator scans only skills/<category>/<name>/SKILL.md; these roles
sit one level deeper. Reuse its parsing rules without changing that validator.
"""

import importlib.util
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit


ROLES_DIR = Path(__file__).resolve().parents[1]
ROOT = ROLES_DIR.parents[2]
SPEC = importlib.util.spec_from_file_location("validate_skills", ROOT / "scripts" / "validate_skills.py")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
ROLE_NAMES = {
    "dev-team-team-lead", "dev-team-planner", "dev-team-fullstack-engineer",
    "dev-team-ai-reviewer", "dev-team-pr-manager", "dev-team-flow-supervisor", "dev-team-squad",
}


class NestedSkillValidationTests(unittest.TestCase):
    def test_all_seven_nested_roles_are_covered(self):
        self.assertEqual({path.parent.name for path in ROLES_DIR.glob("*/SKILL.md")}, ROLE_NAMES)

    def test_nested_role_frontmatter(self):
        for name in sorted(ROLE_NAMES):
            with self.subTest(role=name):
                text = (ROLES_DIR / name / "SKILL.md").read_text(encoding="utf-8")
                fm = VALIDATOR.frontmatter(text)
                self.assertIsNotNone(fm, "missing frontmatter")
                skill_name = VALIDATOR.scalar(fm, "name")
                self.assertEqual(skill_name, name)
                self.assertRegex(skill_name, VALIDATOR.NAME_RE)
                self.assertFalse(any(word in skill_name.lower() for word in VALIDATOR.RESERVED))
                description = VALIDATOR.scalar(fm, "description")
                self.assertTrue(description, "missing or empty description")
                self.assertLessEqual(len(description), 1024)

    def test_nested_role_local_relative_references_exist(self):
        for name in sorted(ROLE_NAMES):
            skill = ROLES_DIR / name / "SKILL.md"
            text = skill.read_text(encoding="utf-8")
            for target in re.findall(r"\]\(([^)]+)\)", text):
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                with self.subTest(role=name, target=target):
                    self.assertTrue((skill.parent / unquote(parsed.path)).is_file(),
                                    f"broken local reference: {target}")


if __name__ == "__main__":
    unittest.main()

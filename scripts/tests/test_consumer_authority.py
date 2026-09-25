"""Regression guards for the agent-facing consumer-upgrade instructions.

These check the published recipe text, not agent execution or provider admission.
Run with: python3 -m unittest discover -s scripts/tests -v
"""
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECIPES = {
    "repo-kit": ("skills/repo/repo-kit/SKILL.md", "## adopt：", "## split："),
    "shared-release": ("skills/workflow/shared-release/SKILL.md", "## 3.", "## 4."),
}


def consumer_instructions(name):
    path, start, end = RECIPES[name]
    return ROOT.joinpath(path).read_text().split(start, 1)[1].split(end, 1)[0]


class ConsumerAuthorityTests(unittest.TestCase):
    def test_upgrade_uses_dependency_authorities_not_agents_inventory(self):
        for name in RECIPES:
            with self.subTest(recipe=name):
                instructions = consumer_instructions(name)
                self.assertNotRegex(instructions, r"AGENTS(?:\.md)?`?\s*依赖段")
                self.assertRegex(instructions, r"manifest/lockfile/caller")
                self.assertRegex(instructions, r"AGENTS.*(?:目录|链接)")

    def test_upgrade_preserves_pin_parity_and_released_provider_compatibility(self):
        for name in RECIPES:
            with self.subTest(recipe=name):
                instructions = consumer_instructions(name)
                self.assertRegex(instructions, r"caller.*协议链接.*完整 SHA.*一致")
                self.assertRegex(instructions, r"旧固定版本.*(?:合同|验证)")
                self.assertRegex(instructions, r"仅在.*已发布版本支持.*机器元数据")
                self.assertIn("不绕过 audit", instructions)
                self.assertRegex(instructions, r"重要 PR")


if __name__ == "__main__":
    unittest.main()

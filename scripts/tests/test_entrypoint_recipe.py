"""Source-contract guards, not proof of agent behavior or live provider adoption."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/repo/repo-kit/SKILL.md"
REFERENCE = SKILL.parent / "references/entrypoint.md"


class EntrypointRecipeTests(unittest.TestCase):
    def setUp(self):
        self.skill = SKILL.read_text(encoding="utf-8")

    def reference(self):
        self.assertTrue(REFERENCE.is_file(), "init needs its disclosed entrypoint contract")
        return REFERENCE.read_text(encoding="utf-8")

    def test_init_reads_reference_before_generation(self):
        init = self.skill.split("## init：", 1)[1].split("## adopt：", 1)[0]
        self.assertIn("[入口合同](references/entrypoint.md)", init)
        self.assertLess(init.index("references/entrypoint.md"), init.index("1. **探测**"))

    def test_example_is_conditional_links_not_embedded_policy(self):
        reference = self.reference()
        example = re.search(r"```markdown\n(.*?)\n```", reference, re.S)
        self.assertIsNotNone(example)
        lines = example.group(1).splitlines()
        self.assertLessEqual(len(lines), 150)
        for line in lines:
            if line and not line.startswith("#"):
                self.assertRegex(line, r"^- [^:\n]+: \[[^\]]+\]\([^\s)]+\)\.$")
        for route in ("docs/architecture/tech-context.md", "docs/development.md",
                      ".github/workflows/ci.yml", "<provider-sha>/ai/agent-protocol.md"):
            self.assertIn(route, example.group(1))
        self.assertNotRegex(reference, r"/blob/[0-9a-f]{40}/")

    def test_real_dependency_authorities_precede_format_selection(self):
        reference = self.reference()
        for term in ("manifest", "lockfile", "caller", "Package.resolved",
                     "package-lock.json", "版本文档", "完整 SHA"):
            self.assertIn(term, reference)
        self.assertLess(reference.index("## 1. 实际权威"), reference.index("## 2. 版本分支"))
        self.assertIn("不从 AGENTS 正文推断依赖", reference)

    def test_metadata_and_legacy_are_distinct_capability_paths(self):
        reference = self.reference()
        for term in ("### Metadata-aware", ".github/repo-contract.json",
                     "schema", "guide", "shared_ci", "dependencies",
                     "### Legacy", "Read first", "Protocol", "Verify",
                     "Required checks", "Red lines", "Delivery",
                     "模板/bootstrap", "不绕过 audit", "版本迁移依赖"):
            self.assertIn(term, reference)
        self.assertIn("所选完整 SHA", reference)
        self.assertIn("不代表模板/bootstrap 已迁移", reference)

    def test_tool_free_reviewer_gets_real_protected_rules(self):
        reference = self.reference()
        for term in ("tool-free", "不会展开", "rules-file", "Codex", "Kimi",
                     "tracked", "trusted-base", "CODEOWNERS", "最后匹配",
                     "实际规则正文", "Owner"):
            self.assertIn(term, reference)

    def test_setup_does_not_claim_protection_from_source(self):
        reference = self.reference()
        for term in ("setup hold", "有效 required checks", "当前 PR head SHA",
                     "实际发出的 check", "原有 required", "dry-run", "readback",
                     "不可读取", "未运行", "不是部署授权"):
            self.assertIn(term, reference)

    def test_repository_ownership_and_test_approval_stay_unchanged(self):
        self.assertIn("从稳定职责、接口与依赖确定边界", self.skill)
        self.assertIn("引用 layer 的路径权威，不复制第二套 globs", self.skill)
        reference = self.reference()
        for term in ("普通测试", "理由", "CI", "AI review",
                     "不因测试编辑或删除新增 Owner", "policy/gate/pin/permission"):
            self.assertIn(term, reference)

    def test_registry_discloses_reference_without_new_skill(self):
        registry = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))
        entries = [item for item in registry["skills"] if item["name"] == "repo-kit"]
        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0]["has_references"])


if __name__ == "__main__":
    unittest.main()

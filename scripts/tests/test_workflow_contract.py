"""Textual regression guards, not a claim of successful behavioral evaluation."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISSUE = ROOT / "skills/repo/multica-issue"


class WorkflowContractTests(unittest.TestCase):
    def test_no_execution_recipe_bypasses_hooks_or_owner_checkout(self):
        for path in ISSUE.rglob("*.md"):
            text = path.read_text()
            for block in re.findall(r"```(?:bash|sh)\n(.*?)```", text, re.S):
                with self.subTest(path=path):
                    self.assertNotRegex(block, r"git (?:commit|push)[^\n]*--no-verify")
                    self.assertNotRegex(block, r"git (?:stash|checkout|switch)\b")
                    self.assertNotIn("gh pr merge", block)

    def test_dispatch_is_fail_closed_and_has_all_active_states(self):
        text = (ISSUE / "references/multica-cli.md").read_text()
        dispatch = text.split("## dispatch / 收尾", 1)[1]
        for marker in ("--active", "--siblings", "--no-start", "queued", "dispatched",
                       "running", "waiting_local_directory", "无效 JSON", "不是空列表",
                       "调用前立即再查", "Owner hold", "一次", "PR Manager"):
            with self.subTest(marker=marker):
                self.assertIn(marker, dispatch)

    def test_creation_and_assignment_flags_are_distinct(self):
        text = (ISSUE / "references/multica-cli.md").read_text()
        self.assertIn("`--assignee` / `--assignee-id`", text)
        self.assertIn("`--to` / `--to-id`", text)
        self.assertIn("--allow-external-file", text)
        self.assertNotIn("workspace switch", text)

    def test_isolation_tail_keeps_verify_and_w4(self):
        text = (ISSUE / "references/issue-templates.md").read_text()
        tail = text.split("## Working Directory(CRITICAL", 1)[1].split("```", 1)[0]
        for marker in ("唯一 writer", "Owner checkout", "AGENTS.md", "scripts/verify", "PR Manager"):
            self.assertIn(marker, tail)
        self.assertNotIn("--no-verify", tail)

    def test_hold_and_outcome_remain_non_dispatching(self):
        text = (ISSUE / "SKILL.md").read_text()
        self.assertIn("user-invocable: true", text)
        self.assertNotIn("disable-model-invocation", text)
        outcome = text.split("### 路径 D", 1)[1].split("## 第 4 步", 1)[0]
        for marker in ("backlog", "不 assign Dev Team", "不转 `todo`", "不调用 `rerun`"):
            self.assertIn(marker, outcome)
        self.assertIn("前置批准、依赖、运行状态均已核验就绪", text)

    def test_missing_design_requires_merge_and_readback(self):
        text = (ISSUE / "references/multica-cli.md").read_text()
        gate = text.split("## spec 先入库门禁", 1)[1].split("## dispatch", 1)[0]
        for marker in ("git fetch", "git cat-file -e", "fetch 成功", "Owner checkout",
                       "scripts/verify", "PR Manager", "merged", "逐路径复核"):
            self.assertIn(marker, gate)


if __name__ == "__main__":
    unittest.main()

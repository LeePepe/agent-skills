"""Textual regression guards, not a claim of successful behavioral evaluation."""
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISSUE = ROOT / "skills/repo/multica-issue"


class DispatchSafetyTests(unittest.TestCase):
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

    def test_planning_consumes_repository_authority(self):
        for path in (ISSUE / "SKILL.md", ISSUE / "references/speckit-bridge.md"):
            with self.subTest(path=path):
                text = path.read_text()
                self.assertIn("仓库定义", text)
                self.assertNotIn("一层一 commit", text)
                self.assertNotIn("跨 2+ layer = 太大", text)
                self.assertNotIn("各自可独立 `swift build/test`", text)
        text = (ISSUE / "SKILL.md").read_text()
        self.assertIn("PRM 不新增范围", text)

    def test_local_reference_links_exist(self):
        for path in [ISSUE / "SKILL.md", *ISSUE.joinpath("references").glob("*.md")]:
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text()):
                if "://" in target or target.startswith("#"):
                    continue
                target = target.split("#", 1)[0]
                with self.subTest(path=path, target=target):
                    self.assertTrue((path.parent / target).exists())


class DesignBaselineProbeTests(unittest.TestCase):
    """Execute only the documented Git read probe in disposable local repositories."""

    def test_fresh_fetch_missing_design_and_failed_fetch_preserve_checkout(self):
        with tempfile.TemporaryDirectory(prefix="dispatch-probe-") as directory:
            root = Path(directory)
            upstream, caller = root / "upstream", root / "caller"
            env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
            env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                       GIT_AUTHOR_NAME="Fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
                       GIT_COMMITTER_NAME="Fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid",
                       GIT_TERMINAL_PROMPT="0")

            def git(cwd, *args):
                return subprocess.run(["git", *args], cwd=cwd, env=env, text=True,
                                      capture_output=True, check=True, timeout=15).stdout

            upstream.mkdir()
            git(upstream, "init", "-q", "-b", "trunk")
            (upstream / "tracked.txt").write_text("baseline\n")
            git(upstream, "add", ".")
            git(upstream, "commit", "-qm", "baseline")
            git(root, "clone", "-q", str(upstream), str(caller))
            git(caller, "remote", "rename", "origin", "source")
            git(caller, "switch", "-qc", "owner-work")
            (caller / "tracked.txt").write_text("staged\n")
            git(caller, "add", "tracked.txt")
            (caller / "tracked.txt").write_text("unstaged\n")
            (caller / "untracked.txt").write_text("preserve\n")
            before = (git(caller, "symbolic-ref", "HEAD"),
                      git(caller, "diff", "--cached"), git(caller, "diff"),
                      git(caller, "status", "--porcelain"))
            (upstream / "spec.md").write_text("# New design\n")
            git(upstream, "add", "spec.md")
            git(upstream, "commit", "-qm", "design")
            text = (ISSUE / "references/multica-cli.md").read_text()
            gate = text.split("## spec 先入库门禁", 1)[1].split("## dispatch", 1)[0]
            probe = re.search(r"```bash\n(.*?)```", gate, re.S).group(1)
            for scenario, path, broken_remote, expected in (
                    ("newly-fetched-design", "spec.md", False, 0),
                    ("missing-design", "absent.md", False, 1),
                    ("failed-fetch-stale-ref", "spec.md", True, 1)):
                with self.subTest(scenario=scenario):
                    if broken_remote:
                        git(caller, "remote", "set-url", "source", str(root / "absent-remote"))
                    result = subprocess.run(["bash", "-c", probe], cwd=caller,
                                            env=dict(env, REMOTE_NAME="source", DEFAULT_BRANCH="trunk",
                                                     SPEC_PATH=path), text=True, capture_output=True,
                                            timeout=15)
                    if expected == 0:
                        self.assertEqual(0, result.returncode, result.stderr)
                    else:
                        self.assertNotEqual(0, result.returncode)
                    after = (git(caller, "symbolic-ref", "HEAD"),
                             git(caller, "diff", "--cached"), git(caller, "diff"),
                             git(caller, "status", "--porcelain"))
                    self.assertEqual(before, after)
                    self.assertEqual("preserve\n", (caller / "untracked.txt").read_text())


if __name__ == "__main__":
    unittest.main()

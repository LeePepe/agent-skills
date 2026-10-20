"""Regression assertions for the frozen Goal/Target/Task v2 role policies."""

from pathlib import Path
import unittest


ROLES_DIR = Path(__file__).resolve().parents[1]


def policy(role):
    return " ".join((ROLES_DIR / f"dev-team-{role}" / "SKILL.md").read_text().split())


class GoalTargetTaskV2Tests(unittest.TestCase):
    def assert_clauses(self, role, *clauses):
        text = policy(role)
        for clause in clauses:
            with self.subTest(role=role, clause=clause):
                self.assertIn(clause, text)

    def test_squad_covers_every_issue_lifecycle_item(self):
        text = policy("squad")
        for item in ("Assignees", "Create", "Dispatch", "PR ownership", "After merge",
                     "Close Task", "Close Target", "Close Goal", "Changes", "Review entry", "Rounds"):
            with self.subTest(item=item):
                self.assertIn(f"**{item}**", text)
        self.assert_clauses(
            "squad", "Goal → Target → Task issues", "one fixed FS writer",
            "several small, single-purpose PRs", "TL decides Target changes",
            "Goal changes return to Owner", "only the last PR checks cumulative Task acceptance",
        )
        for obsolete in ("a human", "lead main agent", "Owner + Team Lead"):
            self.assertNotIn(obsolete, text)

    def test_tl_creates_hierarchy_and_dispatches_only_ready_tasks(self):
        self.assert_clauses(
            "team-lead", "Goal and Target issues are assigned to TL",
            "each Task issue is assigned to its fixed FS",
            "multica issue create --parent <Goal>", "--parent <Target>", "--stage <n>",
            "Dispatch only ready Tasks with no unfinished prerequisites",
            "only after the whole group finishes; it does not automatically dispatch the next group",
            "multica issue children <Target>", "check dependencies and acceptance state",
            "Individual Task handoff and closure do not wait for the group",
            "parallel Tasks use separate FS runs and worktrees",
        )

    def test_closure_requires_all_task_prs_and_independent_acceptance(self):
        self.assert_clauses(
            "team-lead", "all specified outputs exist; every acceptance command passes",
            "all included PRs legally merged",
            "AI Reviewer's last-PR cumulative Task acceptance PASS",
            "all Task issues closed", "exact merged default-branch SHA",
            "Target acceptance-command evidence", "AI Reviewer returns Target-wide PASS to TL",
            "all Targets closed; Goal-level acceptance has evidence",
            "TL closes the Goal issue and notifies Owner with the verdict, evidence and remaining limits",
        )
        self.assert_clauses(
            "squad", "every included PR is legally merged",
            "passed cumulative Task acceptance", "TL closes the Target only on PASS",
            "after all Targets close and Goal-level acceptance has evidence, TL closes the Goal issue",
            "and notifies Owner with the verdict, evidence and remaining limits",
        )
        self.assert_clauses(
            "pr-manager", "Never change Task, Target or Goal status; TL owns Task/Target closure",
            "TL closes the Goal and notifies Owner with the verdict, evidence and remaining limits",
        )

    def test_planner_decides_task_delta_and_only_prepares_target_delta(self):
        self.assert_clauses(
            "planner", "define each Target's Tasks and acceptance commands",
            "Map Goal → Target → Task issues; TL creates the children after review",
            "Decide Task changes only when Target scope and acceptance stay unchanged, and issue a revision",
            "Target changes are TL's decision (Owner when needed)",
            "prepare that revision without deciding it", "Goal changes return to Owner",
        )

    def test_fs_owns_one_frozen_task_and_delegates_only_internal_shards(self):
        self.assert_clauses(
            "fullstack-engineer", "Contract role: Task 写者.",
            "several small PRs, each with one purpose", "each PR linked to the Task issue",
            "delegate execution shards within your Task", "for one level only; no new formal Tasks",
            "frozen Task, owned-path subset, allowed operations and verification commands",
            "Subagents do not commit, push, touch Multica or contact other roles",
            "Task's sole writer", "do not change the definition",
            "whether it is the Task's last PR", "cumulative Task acceptance-command evidence on the last PR",
        )

    def test_reviewer_scopes_pr_task_and_target_acceptance(self):
        self.assert_clauses(
            "ai-reviewer", "from Planner Lead, Fullstack Engineer or Team Lead",
            "this PR's declared single purpose within its frozen Task",
            "Only the Task's last PR checks cumulative Task acceptance across all its PRs",
            "do not require each PR to complete the Target",
            "TL supplies the frozen Target, all closed Task issues, exact merged default-branch SHA",
            "Target acceptance-command evidence", "Return the verdict to TL",
            "check acceptance-command evidence item by item; missing required evidence cannot pass",
            "do not rerun or adjudicate build/test/lint/hooks/CI",
        )
        rubric = " ".join((ROLES_DIR / "dev-team-ai-reviewer" / "references" /
                            "review-rubric.md").read_text().split())
        self.assertIn("the last PR additionally checks cumulative Task acceptance", rubric)
        self.assertIn("missing required evidence cannot pass", rubric)

    def test_target_verdict_has_marker_and_tl_return_route(self):
        self.assert_clauses(
            "ai-reviewer", "gate=<spec|impl|target>", "`gate=target` for TL's job (c)",
            "`[@Team Lead](mention://agent/<Team Lead agent ID>)`",
            "exactly one machine-readable line immediately before the requester mention",
        )
        self.assert_clauses(
            "flow-supervisor",
            "AI Reviewer verdict (spec, impl or target)",
            "the requester named in the verdict (Planner, FS or TL)",
            "Team Lead Target-wide acceptance request, no AI Reviewer run | AI Reviewer",
        )

    def test_prm_uses_task_issue_for_intake_sweep_receipt_and_delivery(self):
        self.assert_clauses(
            "pr-manager", "the Dev Team Task issue and its Task → Target → Goal parent mapping",
            "Start from Dev Team Task issues", "Reuse the Dev Team Task issue and its receipt/state",
            "Post one receipt on the Task issue", "Final report on the Dev Team Task issue to Team Lead",
            "confirm TL received the handoff", "Never change Task, Target or Goal status",
            "once no remaining Task work uses them; preserve the registered Task checkout between its PRs",
        )
        self.assertNotIn("Dev Team Target issue", policy("pr-manager"))
        self.assertNotIn("Close an existing PR-only tracking issue", policy("pr-manager"))

    def test_prm_backfills_external_merges_without_check_changes_idempotently(self):
        self.assert_clauses(
            "pr-manager", "already accepted team PR that is legally merged",
            "Task still open and no final delivery report",
            "even if checks/reviews did not change", "merges by Owner or any other identity",
            "Reuse the existing report/receipt to avoid duplicate reports or dispatches",
            "legal merge by Owner or another identity requires the same final handoff",
            "receipt/run state before retrying so the handoff remains idempotent",
        )

    def test_round_history_is_task_scoped_and_execution_errors_are_separate(self):
        for role in ("team-lead", "fullstack-engineer", "pr-manager", "ai-reviewer"):
            with self.subTest(role=role):
                text = policy(role).lower()
                self.assertIn("same problem × same task", text)
                self.assertIn("at most two", text)
                self.assertIn("changing pr, sha, agent, run or task name does not reset history", text)
                self.assertIn("target-wide acceptance has its own two-round budget", text)
                self.assertIn("separate budget", text)
                self.assertIn("do not count as review rounds", text)
                for obsolete in ("cumulative per pr", "cumulative per repo/pr", "per issue/pr"):
                    self.assertNotIn(obsolete, text)
        for role in ("team-lead", "fullstack-engineer", "pr-manager"):
            self.assert_clauses(role, "at most 2 reruns of the same error, platform retries included")

    def test_workflow_index_uses_task_writers_and_tl_closure(self):
        text = (ROLES_DIR.parent / "README.md").read_text()
        for clause in ("每 Task 一个写者", "PR 关联 Task issue", "最后一个 PR 累计核对 Task 验收",
                       "TL 关闭 Task", "TL 关闭 Target", "TL 关闭 Goal，并通知 Owner 结论、证据与剩余限制",
                       "PRM 不改三层状态"):
            with self.subTest(clause=clause):
                self.assertIn(clause, text)


if __name__ == "__main__":
    unittest.main()

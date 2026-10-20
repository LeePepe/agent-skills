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
        self.assert_clauses(
            "squad", "Contract definitions and V1 supply completion and acceptance conditions",
            "**Assignees**", "**Create / Dispatch**", "**PR ownership**", "**After merge**",
            "**Close Task / Target / Goal**", "**Changes**", "**Review entry**", "**Rounds**",
            "../dev-team-team-lead/SKILL.md#issue-hierarchy-and-dependencies",
            "../dev-team-team-lead/SKILL.md#stage-routing",
            "../dev-team-pr-manager/SKILL.md#ship-confirm-clean-up",
        )
        for obsolete in ("a human", "lead main agent", "Owner + Team Lead"):
            self.assertNotIn(obsolete, policy("squad"))

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
            "team-lead", "contract Task completion + V1 cumulative acceptance satisfied",
            "all Task issues closed", "exact merged default-branch SHA",
            "Target acceptance-command evidence", "AI Reviewer returns Target-wide PASS to TL",
            "all Target issues closed; contract Goal completion and Goal-level acceptance evidence satisfied",
            "TL closes the Goal issue and notifies Owner with the verdict, evidence and remaining limits",
        )
        self.assert_clauses(
            "squad", "Contract definitions and V1 supply completion and acceptance conditions",
            "TL owns lifecycle status changes and the closure actions",
            "../dev-team-team-lead/SKILL.md#stage-routing",
        )
        self.assert_clauses(
            "pr-manager", "Never change Task, Target or Goal status",
            "../dev-team-team-lead/SKILL.md#stage-routing",
        )

    def test_planner_decides_task_delta_and_only_prepares_target_delta(self):
        self.assert_clauses(
            "planner", "**Map** the assigned definition under contract R1–R5",
            "../dev-team-squad/SKILL.md#how-dev-team-uses-goal-target-task",
            "Hand the reviewed mapping to TL for child creation",
        )
        self.assert_clauses(
            "squad", "| Target definer | Planner under R1–R5 |",
            "| Coordinator (including R4 Target-change decisions) | TL; Goal-scope changes go to Owner |",
            "| Goal definer | Owner confirms the Goal; Planner may prepare it under R1 |",
        )

    def test_fs_owns_one_frozen_task_and_delegates_only_internal_shards(self):
        self.assert_clauses(
            "fullstack-engineer", "Contract role: Task 写者.", "under contract R2",
            "each PR linked to the Task issue", "For delegation use contract R6",
            "../dev-team-squad/SKILL.md#how-dev-team-uses-goal-target-task",
            "**Implement** under contract R2–R5", "whether it is the Task's last PR",
            "cumulative Task acceptance-command evidence on the last PR",
        )
        self.assert_clauses("squad", "subagents do not commit, push, touch Multica",
                            "or contact other roles")

    def test_reviewer_scopes_pr_task_and_target_acceptance(self):
        self.assert_clauses(
            "ai-reviewer", "from Planner Lead, Fullstack Engineer or Team Lead",
            "apply contract V1–V2 directly", "for the requested review unit",
            "TL supplies the frozen Target, all closed Task issues, exact merged default-branch SHA",
            "Target acceptance-command evidence", "Return the verdict to TL",
            "Apply contract V1 to each acceptance-command result provided by executor/CI",
            "including cumulative Task evidence when required",
            "you never run or judge build/test/lint/hook/CI gates",
        )
        rubric = " ".join((ROLES_DIR / "dev-team-ai-reviewer" / "references" /
                            "review-rubric.md").read_text().split())
        self.assertIn("Apply contract V1 to the review unit and command evidence", rubric)
        self.assertIn("../SKILL.md#trigger-and-inputs", rubric)

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
                text = policy(role)
                self.assertIn("contract V3", text)
                self.assertIn("../dev-team-squad/SKILL.md#retry-budgets", text)
                for obsolete in ("cumulative per PR", "cumulative per repo/PR", "per issue/PR"):
                    self.assertNotIn(obsolete, text)
        self.assert_clauses(
            "squad", "Review/repair round accounting is authoritative in contract V3",
            "unknown counts block retry (not tracking)",
            "Execution errors (infrastructure, timeout, etc.) have a separate budget",
            "at most 2 reruns of the same error, platform retries included",
            "actor/run/SHA changes do not reset it", "do not count as review rounds",
        )

    def test_workflow_index_uses_task_writers_and_tl_closure(self):
        text = (ROLES_DIR.parent / "README.md").read_text()
        for target in ("dev-team-squad/SKILL.md", "dev-team-team-lead/SKILL.md",
                       "dev-team-fullstack-engineer/SKILL.md", "dev-team-ai-reviewer/SKILL.md",
                       "dev-team-pr-manager/SKILL.md"):
            with self.subTest(target=target):
                self.assertIn(target, text)
        self.assertIn("三层关闭及 Goal 通知 Owner", text)
        self.assertIn("三层定义、R1–R6、交接和 V1–V4", text)


if __name__ == "__main__":
    unittest.main()

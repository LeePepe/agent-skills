"""Behavior tests for Dev Team role policies: Flow Supervisor and PR Manager.

Covers:
- Flow Supervisor workspace routing and issue scan prioritization/exclusion
- PR Manager Dev Team provenance and cancellation safeguards
- PR Manager revisit eligibility, concurrent ownership, and required-check waits
- Immediate auto-merge and merge read-back requirements in the published role instructions
- PR Manager follow-up-only sweeps and missing-handoff TL reminders
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set
import unittest

ROLES_DIR = Path(__file__).resolve().parents[1]
FLOW_SUPERVISOR_SKILL = ROLES_DIR / "dev-team-flow-supervisor" / "SKILL.md"
PR_MANAGER_SKILL = ROLES_DIR / "dev-team-pr-manager" / "SKILL.md"


class IssueStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"


@dataclass
class Issue:
    id: str
    project_id: str
    status: IssueStatus
    title: str
    is_dev_team: bool = True
    labels: List[str] = field(default_factory=list)
    has_active_run: bool = False
    last_run_completed_seconds_ago: Optional[int] = None
    is_blocked: bool = False
    is_lawful_wait: bool = False


@dataclass
class Project:
    id: str
    workspace_id: str
    bound_to_autopilot: bool = False


@dataclass
class PR:
    number: int
    repo: str
    head_sha: str
    is_draft: bool = False
    checks_changed: bool = False
    reviews_changed: bool = False
    gates_pass: bool = False
    infra_failure: bool = False
    has_concrete_finding: bool = False


@dataclass
class SweepReceipt:
    pr_number: int
    head_sha: str
    status: str
    recorded_at: str


@dataclass
class ActiveRun:
    run_id: str
    agent_role: str  # "pr_manager", "fullstack_engineer", etc.
    pr_number: int


# Policy logic simulation engines for behavior verification


def flow_supervisor_collect_scan_targets(
    workspace_id: Optional[str],
    all_projects: List[Project],
    all_issues: List[Issue],
) -> List[Issue]:
    """Models Flow Supervisor workspace routing and scan targeting rules."""
    if not workspace_id:
        raise ValueError("Missing or ambiguous workspace routing input")

    workspace_project_ids = {p.id for p in all_projects if p.workspace_id == workspace_id}

    # Filter to non-terminal Dev Team issues belonging to any project in the workspace
    eligible = []
    for issue in all_issues:
        if issue.project_id not in workspace_project_ids:
            continue
        # Only scan Dev Team issues
        if not issue.is_dev_team:
            continue
        # Red line: Never touch done or cancelled issues
        if issue.status in (IssueStatus.DONE, IssueStatus.CANCELLED):
            continue
        eligible.append(issue)

    # Prioritization: in_review / in_progress first, then todo (and others)
    priority_order = {
        IssueStatus.IN_REVIEW: 0,
        IssueStatus.IN_PROGRESS: 1,
        IssueStatus.TODO: 2,
        IssueStatus.BLOCKED: 3,
    }

    return sorted(eligible, key=lambda i: priority_order.get(i.status, 99))


def flow_supervisor_is_interrupted(issue: Issue) -> bool:
    """Evaluates whether an issue flow is truly interrupted."""
    if issue.has_active_run:
        return False
    if issue.last_run_completed_seconds_ago is not None and issue.last_run_completed_seconds_ago < 300:
        return False
    if issue.is_lawful_wait or issue.is_blocked:
        return False
    return True


@dataclass
class SweepAction:
    action_type: str  # "remind_tl", "revisit_ship", "revisit_rerun", "revisit_route", "revisit_lawful_wait", "skip"
    reason: str
    pr_number: int


def pr_manager_evaluate_pr(
    pr: PR,
    tracking_issue: Optional[Issue],
    active_runs: List[ActiveRun],
    current_sweep_id: str,
    last_receipt: Optional[SweepReceipt],
) -> SweepAction:
    """Models follow-up eligibility after issue-based Dev Team provenance resolution."""
    # PRs without a Dev Team Task issue are never sweep inputs for GitHub reads.
    if tracking_issue is None or not tracking_issue.is_dev_team:
        return SweepAction("skip", "no_dev_team_issue", pr.number)
    if pr.is_draft:
        return SweepAction("skip", "draft_not_eligible", pr.number)

    # Cancellation safeguard applies before reminders and accepted-PR revisits.
    if tracking_issue and tracking_issue.status == IssueStatus.CANCELLED:
        return SweepAction(
            action_type="skip",
            reason="cancelled_tracking_is_terminal",
            pr_number=pr.number,
        )

    # Concurrent ownership check: skip if another live PR Manager or Fullstack Engineer run owns that PR flow
    # Note: current sweep run does not self-disqualify
    competing_runs = [
        run for run in active_runs
        if run.pr_number == pr.number
        and run.run_id != current_sweep_id
        and run.agent_role in ("pr_manager", "fullstack_engineer")
    ]
    if competing_runs:
        return SweepAction(
            action_type="skip",
            reason="concurrent_ownership_active",
            pr_number=pr.number,
        )

    if last_receipt is None or last_receipt.status != "accepted":
        return SweepAction("remind_tl", "missing_prm_acceptance", pr.number)

    # Check if checks or reviews changed since last receipt
    evidence_changed = pr.checks_changed or pr.reviews_changed
    if not evidence_changed:
        return SweepAction(
            action_type="skip",
            reason="no_change_since_last_receipt",
            pr_number=pr.number,
        )

    # Auto-merge is already enabled; follow the current-head checks to read-back.
    if pr.gates_pass:
        return SweepAction(
            action_type="revisit_ship",
            reason="all_required_gates_passed",
            pr_number=pr.number,
        )

    if pr.infra_failure:
        return SweepAction(
            action_type="revisit_rerun",
            reason="infrastructure_failure_within_budget",
            pr_number=pr.number,
        )

    if pr.has_concrete_finding:
        return SweepAction(
            action_type="revisit_route",
            reason="concrete_finding_to_original_fs",
            pr_number=pr.number,
        )

    return SweepAction(
        action_type="revisit_lawful_wait",
        reason="required_checks_pending",
        pr_number=pr.number,
    )


class FlowSupervisorPolicyTests(unittest.TestCase):
    """Test suite for Dev Team Flow Supervisor policies."""

    def setUp(self):
        self.workspace_id = "ws-test-123"
        self.p_bound = Project(id="proj-bound", workspace_id=self.workspace_id, bound_to_autopilot=True)
        self.p_other = Project(id="proj-other", workspace_id=self.workspace_id, bound_to_autopilot=False)
        self.p_ext = Project(id="proj-ext", workspace_id="ws-other", bound_to_autopilot=False)

    def test_workspace_routing_scans_all_workspace_projects_not_just_bound(self):
        issues = [
            Issue(id="i1", project_id="proj-bound", status=IssueStatus.IN_PROGRESS, title="Bound project task"),
            Issue(id="i2", project_id="proj-other", status=IssueStatus.IN_REVIEW, title="Other project task"),
            Issue(id="i3", project_id="proj-ext", status=IssueStatus.IN_PROGRESS, title="External workspace task"),
        ]
        scanned = flow_supervisor_collect_scan_targets(self.workspace_id, [self.p_bound, self.p_other, self.p_ext], issues)
        scanned_ids = [i.id for i in scanned]

        # Must include both workspace projects and exclude foreign workspace
        self.assertIn("i1", scanned_ids)
        self.assertIn("i2", scanned_ids)
        self.assertNotIn("i3", scanned_ids)

    def test_workspace_scan_filters_dev_team_only_issues(self):
        issues = [
            Issue(id="i-dev", project_id="proj-bound", status=IssueStatus.IN_PROGRESS, title="Dev Team task", is_dev_team=True),
            Issue(id="i-non-dev", project_id="proj-bound", status=IssueStatus.IN_PROGRESS, title="Marketing task", is_dev_team=False),
        ]
        scanned = flow_supervisor_collect_scan_targets(self.workspace_id, [self.p_bound], issues)
        scanned_ids = [i.id for i in scanned]

        self.assertIn("i-dev", scanned_ids)
        self.assertNotIn("i-non-dev", scanned_ids)

    def test_scan_prioritization_and_terminal_exclusion(self):
        issues = [
            Issue(id="i-done", project_id="proj-bound", status=IssueStatus.DONE, title="Done task"),
            Issue(id="i-canc", project_id="proj-other", status=IssueStatus.CANCELLED, title="Cancelled task"),
            Issue(id="i-todo", project_id="proj-bound", status=IssueStatus.TODO, title="Todo task"),
            Issue(id="i-rev", project_id="proj-bound", status=IssueStatus.IN_REVIEW, title="In review task"),
            Issue(id="i-prog", project_id="proj-other", status=IssueStatus.IN_PROGRESS, title="In progress task"),
        ]
        scanned = flow_supervisor_collect_scan_targets(self.workspace_id, [self.p_bound, self.p_other], issues)
        scanned_ids = [i.id for i in scanned]

        # Done and cancelled must never be touched
        self.assertNotIn("i-done", scanned_ids)
        self.assertNotIn("i-canc", scanned_ids)

        # in_review and in_progress must come before todo
        self.assertEqual(scanned_ids, ["i-rev", "i-prog", "i-todo"])

    def test_missing_workspace_routing_fails_closed(self):
        issues = [Issue(id="i1", project_id="proj-bound", status=IssueStatus.TODO, title="Task")]
        with self.assertRaises(ValueError):
            flow_supervisor_collect_scan_targets(None, [self.p_bound], issues)

    def test_interruption_detection_respects_cooldown_active_runs_and_lawful_waits(self):
        # Active run -> not interrupted
        self.assertFalse(flow_supervisor_is_interrupted(
            Issue(id="i1", project_id="proj-bound", status=IssueStatus.IN_PROGRESS, title="Task", has_active_run=True)
        ))
        # Recent run within 5 minutes (300s) -> not interrupted (cooldown)
        self.assertFalse(flow_supervisor_is_interrupted(
            Issue(id="i2", project_id="proj-bound", status=IssueStatus.IN_PROGRESS, title="Task", last_run_completed_seconds_ago=120)
        ))
        # Lawful wait (e.g. required checks running) -> not interrupted
        self.assertFalse(flow_supervisor_is_interrupted(
            Issue(id="i3", project_id="proj-bound", status=IssueStatus.IN_REVIEW, title="Task", is_lawful_wait=True)
        ))
        # Truly interrupted (finished stage, idle > 5 mins, no lawful wait)
        self.assertTrue(flow_supervisor_is_interrupted(
            Issue(id="i4", project_id="proj-bound", status=IssueStatus.IN_REVIEW, title="Task", last_run_completed_seconds_ago=600)
        ))


class PRManagerPolicyTests(unittest.TestCase):
    """Test suite for Dev Team-only follow-up, cancellation and revisit policies."""

    def test_cancellation_safeguard_blocks_followup(self):
        pr = PR(number=101, repo="synthetic-owner/synthetic-repo", head_sha="abc1234", checks_changed=True, gates_pass=True)
        cancelled_issue = Issue(id="iss-canc", project_id="p1", status=IssueStatus.CANCELLED, title="PR 101")

        action = pr_manager_evaluate_pr(
            pr=pr,
            tracking_issue=cancelled_issue,
            active_runs=[],
            current_sweep_id="sweep-1",
            last_receipt=SweepReceipt(pr_number=101, head_sha="old_sha", status="accepted", recorded_at="2026-10-13"),
        )

        # Cancelled tracking must not resume delivery or create duplicate tracking
        self.assertEqual(action.action_type, "skip")
        self.assertEqual(action.reason, "cancelled_tracking_is_terminal")

    def test_pr_without_dev_team_issue_is_ignored(self):
        pr = PR(number=102, repo="synthetic-owner/synthetic-repo", head_sha="abc1234")
        action = pr_manager_evaluate_pr(
            pr=pr,
            tracking_issue=None,
            active_runs=[],
            current_sweep_id="sweep-1",
            last_receipt=None,
        )
        self.assertEqual(action.action_type, "skip")
        self.assertEqual(action.reason, "no_dev_team_issue")

    def test_non_team_issue_never_enters_prm_followup(self):
        pr = PR(number=102, repo="synthetic-owner/synthetic-repo", head_sha="abc1234",
                checks_changed=True, gates_pass=True)
        issue = Issue(id="external", project_id="p1", status=IssueStatus.IN_PROGRESS,
                      title="External PR", is_dev_team=False)
        receipt = SweepReceipt(pr_number=102, head_sha="abc1234", status="accepted", recorded_at="2026-10-19")
        action = pr_manager_evaluate_pr(pr, issue, [], "s1", receipt)
        self.assertEqual(action.action_type, "skip")
        self.assertEqual(action.reason, "no_dev_team_issue")

    def test_missing_acceptance_only_reminds_tl_on_team_issue(self):
        pr = PR(number=102, repo="synthetic-owner/synthetic-repo", head_sha="abc1234",
                checks_changed=True, gates_pass=True)
        issue = Issue(id="team", project_id="p1", status=IssueStatus.IN_REVIEW, title="Team PR")
        action = pr_manager_evaluate_pr(pr, issue, [], "s1", None)
        self.assertEqual(action.action_type, "remind_tl")
        self.assertEqual(action.reason, "missing_prm_acceptance")

    def test_draft_does_not_enter_followup(self):
        pr = PR(number=102, repo="synthetic-owner/synthetic-repo", head_sha="abc1234", is_draft=True)
        issue = Issue(id="team", project_id="p1", status=IssueStatus.IN_REVIEW, title="Team PR")
        action = pr_manager_evaluate_pr(pr, issue, [], "s1", None)
        self.assertEqual(action.action_type, "skip")
        self.assertEqual(action.reason, "draft_not_eligible")

    def test_concurrent_ownership_prevents_competing_revisit_from_other_runs(self):
        pr = PR(number=103, repo="synthetic-owner/synthetic-repo", head_sha="abc1234", checks_changed=True, gates_pass=True)
        active_issue = Issue(id="iss-active", project_id="p1", status=IssueStatus.IN_PROGRESS, title="PR 103")

        # Case A: Live Fullstack Engineer repair run active on this PR
        action_fs = pr_manager_evaluate_pr(
            pr=pr,
            tracking_issue=active_issue,
            active_runs=[ActiveRun(run_id="run-fs-1", agent_role="fullstack_engineer", pr_number=103)],
            current_sweep_id="sweep-1",
            last_receipt=SweepReceipt(pr_number=103, head_sha="abc1234", status="accepted", recorded_at="2026-10-13"),
        )
        self.assertEqual(action_fs.action_type, "skip")
        self.assertEqual(action_fs.reason, "concurrent_ownership_active")

        # Case B: Another live PR Manager run active on this PR
        action_prm = pr_manager_evaluate_pr(
            pr=pr,
            tracking_issue=active_issue,
            active_runs=[ActiveRun(run_id="run-prm-other", agent_role="pr_manager", pr_number=103)],
            current_sweep_id="sweep-1",
            last_receipt=SweepReceipt(pr_number=103, head_sha="abc1234", status="accepted", recorded_at="2026-10-13"),
        )
        self.assertEqual(action_prm.action_type, "skip")
        self.assertEqual(action_prm.reason, "concurrent_ownership_active")

    def test_current_sweep_does_not_self_disqualify(self):
        pr = PR(number=103, repo="synthetic-owner/synthetic-repo", head_sha="abc1234", checks_changed=True, gates_pass=True)
        active_issue = Issue(id="iss-active", project_id="p1", status=IssueStatus.IN_PROGRESS, title="PR 103")

        # Current sweep's own run ID does not self-disqualify
        action_self = pr_manager_evaluate_pr(
            pr=pr,
            tracking_issue=active_issue,
            active_runs=[ActiveRun(run_id="sweep-1", agent_role="pr_manager", pr_number=103)],
            current_sweep_id="sweep-1",
            last_receipt=SweepReceipt(pr_number=103, head_sha="abc1234", status="accepted", recorded_at="2026-10-13"),
        )
        self.assertEqual(action_self.action_type, "revisit_ship")

    def test_revisit_eligibility_requires_evidence_change(self):
        pr = PR(number=104, repo="synthetic-owner/synthetic-repo", head_sha="abc1234", checks_changed=False, reviews_changed=False, gates_pass=True)
        tracked_issue = Issue(id="iss-104", project_id="p1", status=IssueStatus.IN_PROGRESS, title="PR 104")

        action = pr_manager_evaluate_pr(
            pr=pr,
            tracking_issue=tracked_issue,
            active_runs=[],
            current_sweep_id="sweep-1",
            last_receipt=SweepReceipt(pr_number=104, head_sha="abc1234", status="accepted", recorded_at="2026-10-13"),
        )
        self.assertEqual(action.action_type, "skip")
        self.assertEqual(action.reason, "no_change_since_last_receipt")

    def test_revisit_actions_shipping_rerun_routing_and_pending_checks(self):
        tracked_issue = Issue(id="iss-track", project_id="p1", status=IssueStatus.IN_PROGRESS, title="Tracked")
        receipt = SweepReceipt(pr_number=200, head_sha="abc", status="accepted", recorded_at="2026-10-13")

        # Case 1: Required checks pending; auto-merge waits for them.
        pr_pending = PR(number=200, repo="synthetic-owner/synthetic-repo", head_sha="abc", checks_changed=True)
        action = pr_manager_evaluate_pr(pr_pending, tracked_issue, [], "s1", receipt)
        self.assertEqual(action.action_type, "revisit_lawful_wait")
        self.assertEqual(action.reason, "required_checks_pending")

        # Case 2: All gates pass -> ship
        pr_ship = PR(number=200, repo="synthetic-owner/synthetic-repo", head_sha="abc", checks_changed=True, gates_pass=True)
        action = pr_manager_evaluate_pr(pr_ship, tracked_issue, [], "s1", receipt)
        self.assertEqual(action.action_type, "revisit_ship")

        # Case 3: Infra failure -> rerun within budget
        pr_infra = PR(number=200, repo="synthetic-owner/synthetic-repo", head_sha="abc", checks_changed=True, infra_failure=True)
        action = pr_manager_evaluate_pr(pr_infra, tracked_issue, [], "s1", receipt)
        self.assertEqual(action.action_type, "revisit_rerun")

        # Case 4: Concrete finding -> original FS
        pr_find = PR(number=200, repo="synthetic-owner/synthetic-repo", head_sha="abc", reviews_changed=True, has_concrete_finding=True)
        action = pr_manager_evaluate_pr(pr_find, tracked_issue, [], "s1", receipt)
        self.assertEqual(action.action_type, "revisit_route")

    def test_sweep_never_creates_tracking_and_still_revisits_accepted_team_prs(self):
        actions = []
        for number in range(1, 6):
            pr = PR(number=number, repo="synthetic-owner/synthetic-repo", head_sha="new",
                    checks_changed=True, gates_pass=True)
            actions.append(pr_manager_evaluate_pr(pr, None, [], "s1", None))
        for number in range(101, 104):
            pr = PR(number=number, repo="synthetic-owner/synthetic-repo", head_sha="new",
                    checks_changed=True, gates_pass=True)
            issue = Issue(id=f"team-{number}", project_id="p1", status=IssueStatus.IN_REVIEW, title="Team PR")
            receipt = SweepReceipt(pr_number=number, head_sha="old", status="accepted", recorded_at="2026-10-19")
            actions.append(pr_manager_evaluate_pr(pr, issue, [], "s1", receipt))
        self.assertEqual([action.action_type for action in actions], ["skip"] * 5 + ["revisit_ship"] * 3)


class SkillDocumentValidationTests(unittest.TestCase):
    """Validates that role SKILL.md documents contain required contract clauses."""

    def test_all_role_skills_contain_contract_role_binding(self):
        bindings = {
            "dev-team-team-lead": "Contract role: 协调者.",
            "dev-team-planner": "Contract role: Target 定义方.",
            "dev-team-fullstack-engineer": "Contract role: Task 写者.",
            "dev-team-ai-reviewer": "Contract role: 独立验收.",
            "dev-team-pr-manager": "Contract role: 交付.",
            "dev-team-flow-supervisor": "Contract role: none (supervision only).",
            "dev-team-squad": "Contract role mapping:",
        }
        for skill, binding in bindings.items():
            with self.subTest(skill=skill):
                text = (ROLES_DIR / skill / "SKILL.md").read_text(encoding="utf-8")
                binding_lines = [line for line in text.splitlines() if line.startswith(binding)]
                self.assertEqual(len(binding_lines), 1)
                self.assertIn("`goal-target-task` skill", binding_lines[0])

    def test_squad_contains_dev_team_core_bindings_section(self):
        text = (ROLES_DIR / "dev-team-squad" / "SKILL.md").read_text(encoding="utf-8")
        heading = "## How Dev Team uses goal-target-task\n"
        self.assertEqual(text.count(heading), 1)
        section = text.split(heading, 1)[1].split("\n## ", 1)[0]
        self.assertLessEqual(len(section.splitlines()) + 1, 30)
        for binding in (
            "| Goal definer | Owner confirms the Goal; Planner may prepare it under R1 |",
            "| Coordinator (including R4 Target-change decisions) | TL; Goal-scope changes go to Owner |",
            "| Target definer | Planner under R1–R5 |", "| Task writer | FS |",
            "| Independent acceptance | AI Reviewer under V1–V3 |",
            "| Delivery | PRM advances each Dev Team PR to legal merge |",
            "Flow Supervisor supervises only and holds no contract role.",
            "The core's 负责人 is the Owner.",
            "This is the authority for those rules", "contract V4",
        ):
            with self.subTest(binding=binding):
                self.assertIn(binding, section)

    def test_writer_and_reviewer_skills_reference_r6(self):
        for skill in ("dev-team-fullstack-engineer", "dev-team-ai-reviewer"):
            with self.subTest(skill=skill):
                text = (ROLES_DIR / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("R6", text)

    def test_pr_manager_skill_contains_cancellation_safeguard_before_branches(self):
        text = PR_MANAGER_SKILL.read_text(encoding="utf-8")
        sweep = text.split("## Follow-up sweep", 1)[1].split("## Dev Team repair path", 1)[0]
        cancel_pos = sweep.index("cancelled/won't-do")
        for branch in ("- **Missing PRM acceptance**", "- **Missing delivery report**",
                       "- **Already accepted Dev Team PR**"):
            self.assertLess(cancel_pos, sweep.index(branch))

    def test_pr_manager_skill_guards_against_active_fullstack_engineer(self):
        text = PR_MANAGER_SKILL.read_text(encoding="utf-8")
        sweep = text.split("## Follow-up sweep", 1)[1].split("## Dev Team repair path", 1)[0]
        self.assertIn("no other live PR Manager or Fullstack Engineer run owns that PR flow", " ".join(sweep.split()))

    def test_pr_manager_has_no_actions_for_prs_outside_dev_team(self):
        text = " ".join(PR_MANAGER_SKILL.read_text(encoding="utf-8").split())
        self.assertIn("PRM does not handle", text)
        self.assertIn("no tracking issue, receipt, label, comment, repair dispatch or merge", text)
        self.assertIn("Without a Dev Team issue, do not read or process the PR", text)
        for obsolete_rule in (
            "authors (fs or a cli subagent)", "any other source", "follow it to a lawful merge",
            "clear small issue", "5 minutes", "≥30 minutes", "a new tracking issue is",
            "issue=none", "discovery sweep",
        ):
            with self.subTest(obsolete_rule=obsolete_rule):
                self.assertNotIn(obsolete_rule, text.lower())

    def test_pr_manager_sweep_only_follows_existing_team_handoffs(self):
        text = " ".join(PR_MANAGER_SKILL.read_text(encoding="utf-8").split())
        self.assertIn("Read GitHub checks/reviews only for Dev Team PRs already handed to PRM", text)
        self.assertIn("remind TL only on that issue. Do not adopt the PR yourself", text)
        self.assertIn("Never create a `[PR Delivery]` tracking issue", text)
        self.assertIn("Author identity cannot distinguish team and CLI work", text)

    def test_tl_immediately_dispatches_prm_after_fs_returns_pr(self):
        text = (ROLES_DIR / "dev-team-team-lead" / "SKILL.md").read_text(encoding="utf-8")
        shipping = next(line for line in text.splitlines() if line.startswith("| Shipping |"))
        self.assertIn("FS returns a created or updated PR to TL", shipping)
        self.assertIn("Immediately dispatch PRM", shipping)
        self.assertIn("do not wait for checks, a sweep or silence", shipping)
        self.assertIn("or duplicate an active PRM run", shipping)
        self.assertIn("../dev-team-squad/SKILL.md#merge-rules-all-repos", shipping)

    def test_prm_enables_auto_merge_before_checks_and_restores_after_push(self):
        text = " ".join(PR_MANAGER_SKILL.read_text(encoding="utf-8").split())
        adoption = text.split("## Adopt", 1)[1].split("## Merge rules", 1)[0]
        self.assertIn("../dev-team-squad/SKILL.md#merge-rules-all-repos", adoption)
        self.assertIn("read back auto-merge enablement", adoption)
        squad = " ".join((ROLES_DIR / "dev-team-squad" / "SKILL.md").read_text().split())
        merge = squad.split("## Merge rules", 1)[1].split("## Owner decisions", 1)[0]
        self.assertIn("enable GitHub auto-merge on opening, before checks finish", merge)
        self.assertIn("Verify auto-merge remains enabled and restore it if GitHub disabled it", merge)
        self.assertIn("never authority to change settings, rulesets or required checks", merge)

    def test_merge_policy_includes_codeowners_and_shared_repository_changes(self):
        text = " ".join((ROLES_DIR / "dev-team-squad" / "SKILL.md").read_text().split())
        merge = text.split("## Merge rules", 1)[1].split("## Owner decisions", 1)[0]
        for clause in ("Every non-Draft PR", "before checks finish",
                       "No Owner approval, approving review or CODEOWNERS review is a merge prerequisite",
                       "including changes to workflows, gates, review policy or CODEOWNERS itself",
                       "product and shared repositories alike"):
            with self.subTest(clause=clause):
                self.assertIn(clause, merge)
        for role in ("pr-manager", "team-lead", "fullstack-engineer"):
            text = (ROLES_DIR / f"dev-team-{role}" / "SKILL.md").read_text()
            self.assertIn("../dev-team-squad/SKILL.md#merge-rules-all-repos", text)

    def test_prm_ship_requires_merge_read_back_and_cleanup_after_proven_merge(self):
        text = " ".join(PR_MANAGER_SKILL.read_text().split())
        ship = text.split("## Ship, confirm, clean up", 1)[1].split("## Red lines", 1)[0]
        self.assertIn("through automatic merge and read-back", ship)
        self.assertIn("PR state, merge commit, target, final checks", ship)
        self.assertIn("CI green ≠ merged", ship)
        self.assertIn("only task-owned branches/worktrees after a proven merge", ship)

    def test_repair_and_release_routes_do_not_make_owner_a_normal_gate(self):
        prm = " ".join(PR_MANAGER_SKILL.read_text().split())
        tl = " ".join((ROLES_DIR / "dev-team-team-lead" / "SKILL.md").read_text().split())
        squad = " ".join((ROLES_DIR / "dev-team-squad" / "SKILL.md").read_text().split())
        workflow = " ".join((ROLES_DIR.parent / "README.md").read_text().split())
        self.assertIn("after two repair rounds return the unresolved issue through TL to the definer", prm)
        self.assertIn("repeated technical failures return to the definer after the repair limit", tl)
        self.assertIn("it is not a prerequisite for normal merge or release", squad)
        self.assertIn("两轮仍失败交定义方，平台故障交平台维护方与协调者", workflow)

    def test_stuck_signal_proxy_and_danger_hold_rules_are_explicit(self):
        prm = " ".join(PR_MANAGER_SKILL.read_text().split())
        tl = " ".join((ROLES_DIR / "dev-team-team-lead" / "SKILL.md").read_text().split())
        squad = " ".join((ROLES_DIR / "dev-team-squad" / "SKILL.md").read_text().split())
        self.assertIn("prmon-repair-queue/v1", prm)
        self.assertIn("legitimate proxy is allowed only when the original writer is unreachable", prm)
        self.assertIn("stuck-PR bot emits the signal only", prm)
        self.assertIn("open-only: do not enable auto-merge and only summarize/observe", squad)
        self.assertIn("public App Store release", squad)
        self.assertIn("review-vs-recorded-decision conflicts go to TL/definer as a decision question", tl)

    def test_flow_supervisor_skill_specifies_workspace_wide_project_scanning(self):
        text = FLOW_SUPERVISOR_SKILL.read_text(encoding="utf-8")
        normalized = " ".join(text.split())
        self.assertIn("Scan every workspace project that has non-terminal Dev Team issues", normalized)
        self.assertIn("rather than limiting the scan to the Autopilot's bound project", normalized)
        self.assertIn("Never touch done/cancelled issues", normalized)


if __name__ == "__main__":
    unittest.main()

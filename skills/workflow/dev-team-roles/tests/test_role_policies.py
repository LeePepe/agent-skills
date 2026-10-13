"""Behavior tests for Dev Team role policies: Flow Supervisor and PR Manager.

Covers:
- Flow Supervisor workspace routing and issue scan prioritization/exclusion
- PR Manager cancellation safeguard (before both tracked and untracked branches)
- PR Manager revisit eligibility, concurrent ownership, and pending Owner approval
- PR Manager discovery sweep accounting and branch isolation
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
    labels: List[str] = field(default_factory=list)
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
    action_type: str  # "create_tracking", "revisit_ship", "revisit_rerun", "revisit_route", "revisit_lawful_wait", "skip"
    reason: str
    pr_number: int


def pr_manager_evaluate_pr(
    pr: PR,
    tracking_issue: Optional[Issue],
    active_runs: List[ActiveRun],
    current_sweep_id: str,
    last_receipt: Optional[SweepReceipt],
) -> SweepAction:
    """Models PR Manager discovery sweep routing and revisit eligibility."""
    # Step 1: Cancellation safeguard (applies before both branches)
    if tracking_issue and tracking_issue.status == IssueStatus.CANCELLED:
        return SweepAction(
            action_type="skip",
            reason="cancelled_tracking_is_terminal",
            pr_number=pr.number,
        )

    # Step 2: Untracked PR branch
    if tracking_issue is None:
        return SweepAction(
            action_type="create_tracking",
            reason="untracked_pr",
            pr_number=pr.number,
        )

    # Step 3: Already tracked PR revisit branch
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

    # Check if checks or reviews changed since last receipt
    evidence_changed = pr.checks_changed or pr.reviews_changed
    if not evidence_changed:
        return SweepAction(
            action_type="skip",
            reason="no_change_since_last_receipt",
            pr_number=pr.number,
        )

    # Eligible revisit: resume flow based on gates/findings/approval
    if "owner-review" in pr.labels:
        return SweepAction(
            action_type="revisit_lawful_wait",
            reason="pending_owner_approval",
            pr_number=pr.number,
        )

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
            reason="concrete_finding_routed_by_source",
            pr_number=pr.number,
        )

    return SweepAction(
        action_type="skip",
        reason="unhandled_revisit_state",
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
        # Lawful wait (e.g. owner-review or CI running) -> not interrupted
        self.assertFalse(flow_supervisor_is_interrupted(
            Issue(id="i3", project_id="proj-bound", status=IssueStatus.IN_REVIEW, title="Task", is_lawful_wait=True)
        ))
        # Truly interrupted (finished stage, idle > 5 mins, no lawful wait)
        self.assertTrue(flow_supervisor_is_interrupted(
            Issue(id="i4", project_id="proj-bound", status=IssueStatus.IN_REVIEW, title="Task", last_run_completed_seconds_ago=600)
        ))


class PRManagerPolicyTests(unittest.TestCase):
    """Test suite for Dev Team PR Manager discovery, cancellation and revisit policies."""

    def test_cancellation_safeguard_blocks_both_tracked_and_untracked_branches(self):
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

    def test_untracked_pr_routes_to_creation(self):
        pr = PR(number=102, repo="synthetic-owner/synthetic-repo", head_sha="abc1234")
        action = pr_manager_evaluate_pr(
            pr=pr,
            tracking_issue=None,
            active_runs=[],
            current_sweep_id="sweep-1",
            last_receipt=None,
        )
        self.assertEqual(action.action_type, "create_tracking")
        self.assertEqual(action.reason, "untracked_pr")

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

    def test_revisit_actions_shipping_rerun_routing_and_pending_owner_approval(self):
        tracked_issue = Issue(id="iss-track", project_id="p1", status=IssueStatus.IN_PROGRESS, title="Tracked")
        receipt = SweepReceipt(pr_number=200, head_sha="abc", status="accepted", recorded_at="2026-10-13")

        # Case 1: Pending Owner approval (owner-review label)
        pr_owner = PR(number=200, repo="synthetic-owner/synthetic-repo", head_sha="abc", checks_changed=True, labels=["owner-review"])
        action = pr_manager_evaluate_pr(pr_owner, tracked_issue, [], "s1", receipt)
        self.assertEqual(action.action_type, "revisit_lawful_wait")
        self.assertEqual(action.reason, "pending_owner_approval")

        # Case 2: All gates pass -> ship
        pr_ship = PR(number=200, repo="synthetic-owner/synthetic-repo", head_sha="abc", checks_changed=True, gates_pass=True)
        action = pr_manager_evaluate_pr(pr_ship, tracked_issue, [], "s1", receipt)
        self.assertEqual(action.action_type, "revisit_ship")

        # Case 3: Infra failure -> rerun within budget
        pr_infra = PR(number=200, repo="synthetic-owner/synthetic-repo", head_sha="abc", checks_changed=True, infra_failure=True)
        action = pr_manager_evaluate_pr(pr_infra, tracked_issue, [], "s1", receipt)
        self.assertEqual(action.action_type, "revisit_rerun")

        # Case 4: Concrete finding -> route by source
        pr_find = PR(number=200, repo="synthetic-owner/synthetic-repo", head_sha="abc", reviews_changed=True, has_concrete_finding=True)
        action = pr_manager_evaluate_pr(pr_find, tracked_issue, [], "s1", receipt)
        self.assertEqual(action.action_type, "revisit_route")

    def test_revisits_do_not_consume_new_tracking_issue_cap(self):
        # Sweep cap: max 3 new tracking issues per sweep
        # Revisits must not consume this quota
        new_prs = [PR(number=i, repo="synthetic-owner/synthetic-repo", head_sha=f"sha_{i}") for i in range(1, 6)]
        tracked_revisit_prs = [
            PR(number=100 + i, repo="synthetic-owner/synthetic-repo", head_sha=f"sha_r_{i}", checks_changed=True, gates_pass=True)
            for i in range(1, 4)
        ]

        created_count = 0
        revisited_count = 0
        quota_remaining = 3

        # Process new PRs
        for pr in new_prs:
            action = pr_manager_evaluate_pr(pr, None, [], "s1", None)
            if action.action_type == "create_tracking" and quota_remaining > 0:
                created_count += 1
                quota_remaining -= 1

        # Process revisits
        for pr in tracked_revisit_prs:
            iss = Issue(id=f"iss-{pr.number}", project_id="p1", status=IssueStatus.IN_PROGRESS, title=f"PR {pr.number}")
            receipt = SweepReceipt(pr_number=pr.number, head_sha="old", status="accepted", recorded_at="2026-10-13")
            action = pr_manager_evaluate_pr(pr, iss, [], "s1", receipt)
            if action.action_type == "revisit_ship":
                revisited_count += 1

        self.assertEqual(created_count, 3)  # Capped at 3
        self.assertEqual(revisited_count, 3)  # Revisits proceed without being blocked by new issue cap


class SkillDocumentValidationTests(unittest.TestCase):
    """Validates that role SKILL.md documents contain required contract clauses."""

    def test_pr_manager_skill_contains_cancellation_safeguard_before_branches(self):
        text = PR_MANAGER_SKILL.read_text(encoding="utf-8")
        self.assertIn("cancelled/won't-do", text)

        # Confirm cancellation safeguard appears before both bullet branches
        sweep_section = text.split("## Discovery sweep", 1)[1].split("## Routing by PR source", 1)[0]

        # Check order: cancellation statement before - **Untracked PR** and - **Already tracked PR**
        cancel_pos = sweep_section.find("cancelled/won't-do")
        untracked_pos = sweep_section.find("- **Untracked PR**")
        tracked_pos = sweep_section.find("- **Already tracked PR**")

        self.assertNotEqual(cancel_pos, -1, "Cancellation check missing in discovery sweep section")
        self.assertNotEqual(untracked_pos, -1, "Untracked PR branch missing")
        self.assertNotEqual(tracked_pos, -1, "Already tracked PR branch missing")
        self.assertLess(cancel_pos, untracked_pos, "Cancellation safeguard must precede untracked branch")
        self.assertLess(cancel_pos, tracked_pos, "Cancellation safeguard must precede already tracked branch")

    def test_pr_manager_skill_guards_against_active_fullstack_engineer(self):
        text = PR_MANAGER_SKILL.read_text(encoding="utf-8")
        sweep_section = text.split("## Discovery sweep", 1)[1].split("## Routing by PR source", 1)[0]
        self.assertIn("no other live PR Manager or Fullstack Engineer run owns that PR flow", " ".join(sweep_section.split()))

    def test_flow_supervisor_skill_specifies_workspace_wide_project_scanning(self):
        text = FLOW_SUPERVISOR_SKILL.read_text(encoding="utf-8")
        normalized = " ".join(text.split())
        self.assertIn("Scan every workspace project that has non-terminal Dev Team issues", normalized)
        self.assertIn("rather than limiting the scan to the Autopilot's bound project", normalized)
        self.assertIn("Never touch done/cancelled issues", normalized)


if __name__ == "__main__":
    unittest.main()

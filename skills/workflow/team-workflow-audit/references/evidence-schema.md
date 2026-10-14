# Evidence and Finding Schema

Use stable source IDs and UTC timestamps. Redact secrets and unnecessary personal content.

```json
{
  "snapshot_id": "audit:<scope>:<observed_at>",
  "scope": {"owner": "...", "project_id": "...", "repository": "owner/repo"},
  "mode": "baseline|incremental",
  "instruction_versions": [{"source_id": "...", "updated_at": "...", "content_sha256": "..."}],
  "cohort": {"id": "...", "fixed": true, "cases": ["..."]},
  "cursors": [{"source": "...", "timestamp": "...", "stable_id": "...", "overlap_hours": 24}],
  "owner_summary": {
    "total_cases": 0,
    "delivery_trust": {"confirmed_trustworthy": 0, "confirmed_compromised": 0, "unknown": 0},
    "rule_following": {"confirmed_following": 0, "confirmed_violations": 0, "unknown": 0},
    "workflow_usability": {"confirmed_fit": 0, "confirmed_unfit": 0, "unknown": 0},
    "task_effectiveness": {
      "confirmed_effective": 0,
      "confirmed_ineffective": 0,
      "confirmed_regressed": 0,
      "pending": 0,
      "unknown": 0
    },
    "top_concerns": [],
    "owner_actions": []
  },
  "events": [{"id": "...", "source": "...", "subject_id": "...", "actor_role": "...", "kind": "...", "at": "...", "sha": "...", "evidence_ref": "..."}],
  "feedback_lineage": [{
    "problem_fingerprint": "...",
    "origin_issue_id": "...",
    "delivery_issue_id": "...",
    "pr_url": "...",
    "merge_sha": "...",
    "release_channel": "testflight|app_store|production|internal",
    "first_version": "...",
    "first_build": "...",
    "available_at": "...",
    "observation_events": ["..."],
    "related_feedback_issue_ids": ["..."],
    "task_effectiveness": "effective|ineffective|regressed|pending_delivery|pending_release|pending_observation|insufficient_evidence"
  }],
  "agent_attempts": [{
    "id": "...",
    "subject_id": "...",
    "actor_role": "planner_lead|team_lead|fullstack_engineer|ai_reviewer|pr_manager",
    "cycle_kind": "...",
    "artifact_id": "...",
    "attempt_index": 1,
    "trigger_cause": "...",
    "started_at": "...",
    "ended_at": "...",
    "outcome": "...",
    "event_ids": ["..."]
  }],
  "agent_repeat_metrics": [{
    "actor_role": "...",
    "attempts_total": 0,
    "repeat_cycles": 0,
    "repeat_cases": 0,
    "same_artifact_repeat_cycles": 0,
    "changed_artifact_repeat_cycles": 0,
    "max_cycles_per_case": 0,
    "by_cycle_kind": {},
    "by_trigger_cause": {},
    "role_specific": {},
    "subject_ids": ["..."],
    "event_ids": ["..."]
  }],
  "findings": [{
    "fingerprint": "<responsibility_layer>|<invariant>|<subject_id>",
    "axis": "workflow_conformance|workflow_fitness|outcome_integrity|task_effectiveness",
    "priority": "P0|P1|P2|info",
    "state": "open|acknowledged|approved_for_remediation|resolved|regressed|superseded",
    "verdict": "...",
    "event_ids": ["..."],
    "responsibility_layer": "...",
    "subject_id": "...",
    "proposed_remediation_owner": "project_dev_team|separate_execution_agent"
  }],
  "limitations": ["..."]
}
```

Evidence absence is not proof of misconduct. Emit `insufficient_evidence` and state what is missing. Preserve source references and hashes, not complete raw daemon/session logs.

Agent attempt identity is `subject_id + actor_role + cycle_kind`. Preserve the role-specific artifact identity from [agent-repeat-metrics.md](agent-repeat-metrics.md); do not collapse all agents into one repeat count.

Every axis inside `owner_summary` must reconcile to `total_cases`. Unknown is not success. Follow [owner-report.md](owner-report.md) for the plain-language report and keep exact enums in the appendix.

Task Effectiveness follows [task-effectiveness.md](task-effectiveness.md). Preserve problem, release/build, and observation identities; do not infer effectiveness from a successful merge or from silence after release.

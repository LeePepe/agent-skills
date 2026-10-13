# Agent Repeat Metrics

Measure repeated workflow activity per owning agent role. Repetition is a Workflow Fitness signal, not proof of a Workflow Conformance violation.

## Counting identity

An attempt belongs to one stable group:

`subject_id + actor_role + cycle_kind`

The first attempt establishes the baseline. Every later attempt in the same group is one `repeat_cycle`.

Use the role-specific artifact identity below. Classify each repeat against the immediately preceding attempt:

- `same_artifact_repeat_cycle`: artifact identity is unchanged;
- `changed_artifact_repeat_cycle`: artifact identity changed.

If the subject, role, cycle kind, or artifact identity cannot be resolved, report `insufficient_evidence` instead of guessing. Count each attempt once under its owning role. Record the triggering cause separately; attribution describes activity, not blame.

Do not compute `unproductive_wake_cycles`.

## Common metrics for every role

Report these separately for each role:

- `attempts_total`: all observed attempts owned by the role;
- `repeat_cycles`: attempts beyond the first in each stable group;
- `repeat_cases`: subjects with at least one repeat cycle;
- `same_artifact_repeat_cycles`: repeats with unchanged artifact identity;
- `changed_artifact_repeat_cycles`: repeats with a new artifact identity;
- `max_cycles_per_case`: highest attempt count for one subject and cycle kind.

Attach the subject IDs and event IDs behind every count. Do not combine roles into a single agent-efficiency score.

## Planner Lead

Artifact identity: exact spec/plan/tasks revision plus reviewed artifact-set hash.

Cycle kinds and role-specific metrics:

- `planning_revision_rounds`: distinct planning revisions submitted for review;
- `planning_review_repeat_cycles`: Reviewer submissions beyond the first;
- `planning_same_revision_re_reviews`: review requests repeated without a new planning revision;
- `planning_handoff_repeat_cycles`: repeated attempts to hand an approved planning package to Team Lead.

## Team Lead

Artifact identity: `blocker_key + intended_next_actor + candidate_sha_or_revision`.

Cycle kinds and role-specific metrics:

- `recovery_dispatch_rounds`: TL recovery dispatches for the same blocker;
- `recovery_dispatch_repeat_cycles`: recovery dispatches beyond the first;
- `same_recovery_key_redispatches`: repeated dispatches with unchanged recovery identity;
- `owner_escalation_repeat_cycles`: repeated Owner escalations for the same unresolved decision identity.

A normal first scheduling or recovery dispatch is not a repeat.

## Fullstack Engineer

Artifact identity: candidate SHA; before the first commit, use the task workdir plus a deterministic diff hash.

Cycle kinds and role-specific metrics:

- `implementation_revision_rounds`: implementation candidates produced;
- `review_fix_rounds`: FS repair rounds triggered by Reviewer blocking findings;
- `ci_repair_rounds`: FS repair rounds triggered by CI or repository-gate failures;
- `same_review_finding_repeats`: the same finding fingerprint survives a prior repair round;
- `same_ci_failure_repeats`: the same normalized CI failure fingerprint survives a prior repair round;
- `handoff_repair_rounds`: repairs required only because SHA, metadata, branch, PR, or workdir identity was incomplete or inconsistent.

## AI Reviewer

Artifact identity: exact reviewed revision plus review-surface hash.

Cycle kinds and role-specific metrics:

- `review_rounds`: all independent review attempts;
- `review_repeat_cycles`: review attempts beyond the first for the same subject and review kind;
- `same_sha_re_reviews`: repeated reviews of the same revision and surface;
- `changed_sha_re_reviews`: repeated reviews after the candidate changed;
- `inconclusive_review_rounds`: reviews ending `INCONCLUSIVE`;
- `changes_requested_rounds`: reviews ending `CHANGES REQUESTED` or `FAIL`.

Planning review and implementation review are separate cycle kinds.

## PR Manager

Artifact identity: reviewed candidate SHA plus required-check set identity.

Cycle kinds and role-specific metrics:

- `ci_supervision_rounds`: bounded CI supervision attempts;
- `ci_supervision_repeat_cycles`: supervision attempts beyond the first for the same candidate;
- `same_sha_ci_reruns`: CI reruns on an unchanged candidate SHA;
- `shipping_attempt_rounds`: ready/auto-merge/merge attempts;
- `shipping_attempt_repeat_cycles`: shipping attempts beyond the first;
- `implementation_return_rounds`: returns to FS caused by a code or repository-gate failure.

Polling inside one bounded PR Manager run is one supervision round, not multiple attempts.

## Cause dimensions

Classify the trigger independently from the owning role:

`planning_finding`, `review_finding`, `ci_code_failure`, `ci_infrastructure_failure`, `sha_or_metadata_mismatch`, `permission_or_credential`, `hardware_or_environment`, `owner_decision`, `workflow_configuration`, or `unknown`.

Report a per-role cause breakdown so repeated Reviewer rounds and repeated FS CI repairs remain distinguishable.

## Judging the axes

- Repetition alone affects Workflow Fitness.
- Emit a Workflow Conformance finding only when evidence shows the role omitted a required action, crossed its authority, repeated an explicitly forbidden dispatch, or violated another cited invariant.
- Outcome Integrity remains independent: repeated rounds may still deliver an intact outcome.

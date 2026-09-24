# Problem History and Outcome Checks

Use this reference for bug reports, repeated symptoms, regressions, and explicit requests to wait for TestFlight or real-use validation.

## Problem fingerprint

Create a stable implementation-independent identity:

`<product_area>|<behavior_or_invariant>|<user_visible_symptom>`

Normalize case and whitespace. Keep user data, secrets, timestamps, versions, and implementation details out of the fingerprint.

Example:

`appui|keyboard-safe-area|active-workout-controls-obscured`

## Search before create

1. Search active and closed history with concise symptom and product-area terms:

   `multica issue search "<query>" --include-closed --output json`

2. Inspect likely matches with `issue get` and `issue metadata get --key problem_fingerprint`.
   Keep candidates in the resolved target project unless cross-project ownership is explicitly part of the problem.
3. Use an exact fingerprint match plus affected release evidence to assign a relationship.
4. Let Multica's duplicate protection stop an active duplicate. Use `--allow-duplicate` only when the new issue is intentionally a distinct recurrence record.

## Relationship rules

- Active exact match: `duplicate_of`.
- Same fingerprint on a build containing a prior fix, without prior effective confirmation: `ineffective_fix_for`.
- Same fingerprint after a prior `confirmed_effective` event: `regression_of`.
- Similar symptom with incomplete build/fingerprint evidence: `related_to`.

Store the current index in metadata:

- `problem_fingerprint`: string;
- `problem_report`: JSON object with `source_kind`, `observed_at`, `affected_version`, `affected_build`, `environment`, and `evidence_ref`;
- `problem_relation`: JSON object with `type` and `issue_id`.
- `task_effectiveness`: initialize the originating Bug to `{"status":"pending_delivery"}`.

Also write the relationship and evidence into the issue body so humans and agents can read it without metadata tooling.

## Delivery exposure

When known, index the first release containing a fix:

- `delivery_issue_id`;
- `pr_url`;
- `merge_sha`;
- `release_channel`;
- `first_version`;
- `first_build`;
- `available_at`.

Release availability proves that observation can begin. It does not prove the task is effective.

## Outcome Check

Create `[Outcome Check] <original issue>: <behavior>` only when post-release use materially determines success, such as TestFlight behavior, hardware integration, telemetry windows, or user-visible regressions.

The Outcome Check is a waiting record, not implementation work:

- status: `backlog`;
- assignee: the explicit wait owner;
- no Dev Team assignment;
- no transition to `todo`;
- no agent run or rerun;
- metadata key `outcome_wait` containing `delivery_issue_id`, `problem_fingerprint`, `wait_owner`, `next_event`, `release_channel`, `release_build`, `not_before`, optional `deadline`, and `wake_condition`.

Use one current outcome index:

- `task_effectiveness.status`: `pending_delivery`, `pending_release`, `pending_observation`, `effective`, `ineffective`, `regressed`, or `insufficient_evidence`;
- `task_effectiveness.observed_at`;
- `task_effectiveness.evidence_ref`.

Record each state change or confirmation as a new comment/timeline event before updating the current metadata index.

## Closing the loop

- Positive use evidence: record `effective`, link the build/evidence, and close the Outcome Check.
- Persistent problem: create a normal bug through the standard dispatched path with `ineffective_fix_for`.
- Reappeared problem: create a normal bug with `regression_of`.
- Deadline without evidence: keep the result unconfirmed; record the missing evidence and retain `pending_observation` or `insufficient_evidence`.

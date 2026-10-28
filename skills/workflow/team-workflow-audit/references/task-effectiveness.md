# Task Effectiveness

Judge whether the delivered work actually solved the originating problem in its real operating context. Keep this axis independent from delivery integrity: a correctly reviewed and merged change may still fail to solve the task.

## Evidence chain

Reconstruct this lineage with stable identities:

`problem report → origin issue → delivery issue/PR/SHA → first containing release/build → exposure or use → feedback evidence → effectiveness verdict`

Required identities when available:

- `problem_fingerprint`;
- origin and delivery issue-tracker item IDs;
- PR and merge SHA;
- release channel, version, and build;
- release availability timestamp;
- observation timestamp and evidence source;
- related feedback issue IDs and relation types.

## Verdicts

- `effective`: the containing release was exercised in the relevant context and positive evidence confirms the originating behavior is corrected.
- `ineffective`: the same problem fingerprint is observed on a release containing the fix, before any confirmed-effective observation.
- `regressed`: the task was confirmed effective, then the same problem fingerprint reappeared on a later release.
- `pending_delivery`: implementation or delivery is still nonterminal.
- `pending_release`: delivery is complete but the first containing release/build is not yet available.
- `pending_observation`: the containing release is available but the required use, telemetry window, or Owner confirmation has not occurred.
- `insufficient_evidence`: release identity, affected build, fingerprint relation, or observation provenance is missing.

An `effective` verdict requires positive exposure evidence. The absence of a later issue remains `pending_observation` or `insufficient_evidence`.

## Problem relationships

Use one relation from the later report to the prior issue:

- `duplicate_of`: the same problem is already active;
- `ineffective_fix_for`: the problem persists on a build containing the fix;
- `regression_of`: the problem was confirmed fixed and later returned;
- `related_to`: similarity exists but the build or fingerprint evidence cannot establish a stronger relation.

Title similarity is discovery evidence only. Confirm relationships with `problem_fingerprint`, affected build, and evidence.

## Observation contract

High-impact or user-visible changes may use a non-execution `[Outcome Check]` issue with:

- `delivery_issue_id`;
- `problem_fingerprint`;
- `wait_owner`;
- `next_event`;
- `release_channel`;
- `release_build` when known;
- `not_before` and optional observation deadline;
- `wake_condition`.

The check waits without dispatching an implementation agent. Record release availability and effectiveness decisions as new evidence events. A negative observation creates a normal bug issue linked to the prior fix.

## Sources

Prefer, in order:

1. Owner or user report with affected release/build and reproducible behavior;
2. production/test telemetry tied to the containing release;
3. controlled post-release validation in the relevant environment;
4. TestFlight/release availability alone, which proves exposure readiness but not effectiveness.

## Findings

Emit a Task Effectiveness finding for `ineffective` or `regressed`. Fingerprint it as:

`project_logic|task_effectiveness|<origin_issue_id>`

Set priority from the original problem's user impact. Pending and insufficient states are reportable counts, not automatic violations.

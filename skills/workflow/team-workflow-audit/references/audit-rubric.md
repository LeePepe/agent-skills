# Audit Rubric

Judge each axis independently and cite event IDs for every verdict.

## Workflow Conformance

Ask whether the observed actors followed the then-current authoritative workflow: correct owner, ordered handoffs, workdir use, SHA continuity, required reviews/CI, and explicit recovery or escalation. Classify `conformant`, `nonconformant`, or `insufficient_evidence`.

## Workflow Fitness

Ask whether the workflow itself is safe and capable of reaching a clear outcome: responsibilities are assigned, executor impediments return to Team Lead, waits have an owner and next event, supersession is explicit, review gates cannot be bypassed, and escalation reaches Owner when Team Lead cannot recover. Classify `fit`, `unfit`, or `insufficient_evidence`.

## Outcome Integrity

Ask whether the delivered result corresponds to the reviewed code and requested outcome: issue/spec acceptance is met, tested SHA equals reviewed/merged SHA, required gates precede merge, and terminal state matches reality. Classify `intact`, `compromised`, or `insufficient_evidence`.

## Task Effectiveness

Ask whether the delivered work actually solved the originating problem in the relevant release and operating context. Reconstruct the problem → delivery → release/build → exposure/use → feedback lineage from [task-effectiveness.md](task-effectiveness.md). Classify `effective`, `ineffective`, `regressed`, `pending_delivery`, `pending_release`, `pending_observation`, or `insufficient_evidence`.

Outcome Integrity and Task Effectiveness are independent: a correctly reviewed and merged change may still be ineffective in TestFlight or real use.

## Required detections

| Invariant | Evidence signal | Default priority |
|---|---|---|
| Active work has an accountable next actor | nonterminal leaf with no live/queued actor and no explicit wait owner | P1 |
| Executor impediments return to Team Lead | executor declares terminal block without TL recovery/escalation | P1 |
| Handoffs preserve the reviewed SHA | implementation/review/merge SHAs differ without a new gate | P0 |
| Required review check precedes merge | merge time is earlier than the passing required review check | P0 |
| Runs have one authoritative successor | concurrent runs overlap without explicit supersession | P1 |
| Autopilot stays inside its control-plane authority | source/config/runtime repair or a gate decision performed by an operations-only supervisor | P1; gate bypass may be P0 |
| Retries preserve intent and budget | stale-HEAD/Owner-cancelled rerun, missing readiness, duplicate dispatch or budget reset on each sweep | P1 |
| Runtime placement is verified | team bound to a stale/wrong machine or scheduler marked operational without an execution probe | P1; unknown when evidence is missing |
| External PR intake has ownership and identity | authorized in-scope PR orphaned solely because it was created outside Dev Team, or adopted without exact-SHA review/workdir evidence | P1; stale delivery may be P0 |
| Workflow protects outcomes | conformant case follows an unsafe/unfinishable rule | P1 fitness finding |
| Protective deviations are visible | deviation prevents unsafe action and is escalated with evidence | informational; not a conformance failure |
| Delivered work solves the reported problem | same problem fingerprint appears on a containing release, or reappears after effective confirmation | P1 effectiveness finding; raise with original impact |

Priority may be raised with evidence. Never lower a P0/P1 solely because the eventual outcome succeeded.

For the added supervision invariants, use [autopilot-contract.md](autopilot-contract.md) and the actual Owner-approved scope/budget. A paused or unavailable runtime with an explicit recovery owner and wake condition is not automatically a violation.

## Metrics

Report counts/rates separately: silent stalls, invalid blocks, SHA handoff failures, premature merges, duplicate/superseding runs, protective deviations, and recovery latency. Do not combine them into one score.

Report agent repetition separately for Planner Lead, Team Lead, Fullstack Engineer, AI Reviewer, and PR Manager using [agent-repeat-metrics.md](agent-repeat-metrics.md). Repetition is a Workflow Fitness signal. It becomes a Workflow Conformance finding only when a cited duty or authority boundary was violated.

Report Task Effectiveness counts separately: effective, ineffective, regressed, pending delivery, pending release, pending observation, and insufficient evidence. Effective requires positive exposure evidence.

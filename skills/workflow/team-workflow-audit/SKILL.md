---
name: team-workflow-audit
description: Audit an explicitly named team, repository, or project delivery workflow against evidence, current instructions, workflow fitness, and delivered outcomes. Use only when the user explicitly invokes $team-workflow-audit or directly asks to run this audit. Never remediate or mutate audited systems.
disable-model-invocation: true
---

# Team Workflow Audit

Perform an evidence-led, read-only audit. Do not change repositories, issues, runs, teams, the control plane, aidata, or AIDash. Show findings and wait for explicit owner approval before any separate remediation work.

## Start

1. Confirm the named scope and audit mode: `baseline` or `incremental`.
2. Read [audit-rubric.md](references/audit-rubric.md), [agent-repeat-metrics.md](references/agent-repeat-metrics.md), [task-effectiveness.md](references/task-effectiveness.md), [owner-report.md](references/owner-report.md), [evidence-schema.md](references/evidence-schema.md), [workflow-authority.md](references/workflow-authority.md), and [aidata-contract.md](references/aidata-contract.md).
3. Resolve repositories and projects from authoritative identifiers; never hardcode a checkout path.
4. Record the current instruction documents only. If the source has no version history, identify each observed version with `updated_at + SHA-256(content)`.
5. When the scope includes scheduled autopilot, runtime migration or adoption of an externally created PR, read [autopilot-contract.md](references/autopilot-contract.md). Audit the control-plane actions separately from Dev Team implementation; this remains a read-only audit.
6. For repeated Owner intervention, preparation/Planner routing, review-stage confusion, or model-capability claims, read [owner-intervention-cases.md](references/owner-intervention-cases.md). Its dated AIDash/VoxPocket/VitalStride decisions supersede older generic role examples only for those projects; establish the authority effective at each event.
7. For AI review false positives on instruction artifacts or claims that Markdown extraction fixes prompt safety, read [prompt-safety-and-semantics.md](references/prompt-safety-and-semantics.md). Audit construction, classification and validation evidence separately; this grants no remediation authority.
8. For the settled AIDash/VoxPocket/VitalStride workflow, read [settled-workflow-state.md](references/settled-workflow-state.md): final role/stage decisions, dated deployment and merge evidence, withdrawn proposals and unverified outcomes. Treat it as an evidence snapshot, not authorization to configure or dispatch.

## Sample

For the first baseline of each project, select a fixed 20-case cohort:

- 10 current nonterminal leaf cases;
- 5 recent successful deliveries;
- 5 abnormal terminal cases.

Keep the baseline cohort separate from the incremental stream. For incremental audits, maintain one `(timestamp, stable ID)` cursor per source, read with a 24-hour overlap, then deduplicate by stable source identity.

## Audit

For every case:

1. Reconstruct an evidence timeline from issue, task/run, agent, workdir, commit/SHA, PR, review, CI, merge, and relevant runtime events.
2. Evaluate four independent axes: Workflow Conformance, Workflow Fitness, Outcome Integrity, and Task Effectiveness. Never infer one axis from another. Use [task-effectiveness.md](references/task-effectiveness.md) for release, TestFlight, use, telemetry, and later-feedback evidence.
3. Compare each action to the authority order. Distinguish a workflow violation from a justified protective deviation from an unfit workflow.
4. Detect silent stalls, invalid executor blocks, stale-SHA handoffs, merge before required review, overlapping or superseding runs, missing ownership, and recovery latency.
5. Give every finding a stable fingerprint: `responsibility layer + invariant + subject ID`.
6. Use the finding lifecycle exactly: `open`, `acknowledged`, `approved_for_remediation`, `resolved`, `regressed`, `superseded`.
7. Do not compute a single aggregate score. Report each metric and its evidence separately.
8. Compute agent repetition per role using [agent-repeat-metrics.md](references/agent-repeat-metrics.md). Keep Planner Lead, Team Lead, Fullstack Engineer, AI Reviewer, and PR Manager metrics separate; preserve artifact identity and trigger cause for every attempt.

An executor/Fullstack Engineer may report an impediment but may not make the case disappear into a terminal blocking state. Responsibility returns to Team Lead, who must recover, reassign, supersede, or escalate to Owner with evidence.

## Visualize

Use Archify workflow artifacts as specified in [archify.md](references/archify.md). Produce or refresh:

- one generic Team Operating Workflow covering delivery and post-release effectiveness feedback;
- one relationship diagram per audited team/repository;
- one current-state event chain for each P0/P1 finding.

The JSON source is authoritative. Validate at `showcase` quality with zero errors and zero warnings before delivery; do not edit it after the final passing validation.

## Report

Write the primary report using [owner-report.md](references/owner-report.md). Lead with reconciled plain-language counts for confirmed trustworthy, confirmed bad, and unknown outcomes. Keep audit enums and evidence mechanics in the technical appendix.

Show the owner:

- scope, cohort/cursor, evidence coverage, and limitations;
- what is confirmed, what remains unknown, and what needs attention now;
- findings grouped by axis and priority;
- explicit workflow-conformance and workflow-fitness judgments;
- delivery-integrity and real-world task-effectiveness judgments kept separate;
- per-role repeat metrics and cause breakdowns;
- case timelines and Archify artifacts;
- proposed remediation owner: project Dev Team for project/repository logic, separate execution agent for project-independent platform/workflow changes.

Render the three delivery/workflow buckets and the four Task Effectiveness groups exactly as [owner-report.md](references/owner-report.md) defines them. Apply its deletion test before delivery.

Approval changes only the finding state. It does not authorize this skill to remediate. AIDash may display snapshots and approval events and may link to `grill-me` or `grill-with-docs`; it must not auto-remediate.

## Open the report in cmux

After the primary Markdown report and all validation artifacts are final, open that report in cmux's formatted Markdown viewer:

```bash
cmux markdown open "/absolute/path/to/primary-report.md" --focus true
```

Use the absolute path of the Owner-facing primary report, not a snapshot, technical appendix, diagram, or interim draft. Run this once per completed audit. A zero exit status is the completion evidence that the report was opened. If `cmux` is unavailable or the command fails, keep the audit result intact and report the exact open failure; never claim the report was opened or regenerate audit content to hide a viewer failure. Opening the report is a presentation action outside the audited systems and does not authorize remediation.

## Validate This Skill

Run:

```bash
python3 scripts/validate_fixtures.py
```

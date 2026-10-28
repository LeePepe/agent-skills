# Workflow Authority and Responsibility

Apply the first applicable authority in this order:

1. non-bypassable platform safety and data constraints;
2. current Owner decisions;
3. repository constitution, accepted ADRs, and root instructions;
4. reviewed spec, plan, tasks, and layer context;
5. team workflow and role instructions;
6. task handoff or trigger comment.

Record conflicts rather than silently choosing a lower authority.

## Responsibility boundary

For AIDash, VoxPocket and VitalStride, apply the [2026-09-18/19 settled decisions](settled-workflow-state.md) before the older role examples below: FS performs first workspace preparation; PR tracking adoption is separate from shipping eligibility. Historical events retain their then-effective rules.

- Owner sets intent, approves remediation, and decides escalations Team Lead cannot resolve.
- Team Lead creates and owns the task workdir, assigns execution, supervises progress, handles executor impediments, and escalates when recovery is impossible.
- Fullstack Engineer/Executor works only in the task workdir, produces implementation/test evidence, and reports impediments to Team Lead. It does not own the terminal blocked decision.
- Reviewers decide their gates and return actionable findings to Team Lead.
- PR/CI actors preserve SHA identity and gate order.
- scheduled autopilot observes, dispatches, performs authorized bounded reruns and reports; Dev Team owns code/config/runtime repair. PR Manager only adopts Dev Team PRs immediately dispatched by TL from the Target issue's FS handoff or delivery information; other PRs remain with their own writers. Apply [autopilot-contract.md](autopilot-contract.md) when auditing supervision, runtime placement or external PR intake.
- Audit Engine observes and reports only.
- AIDash displays audit snapshots and approval events only.
- Owner or an authoritative feedback source confirms post-release effectiveness; merge success alone does not.

Repository/project remediation belongs to its Dev Team. Changes to project-independent workflow/platform machinery belong to a separately authorized execution agent. Never modify the control plane merely to change its product name or unrelated content.

---
name: multica-delivery-supervisor
description: Supervise named Multica projects and delivery PRs, or resume tasks affected by a shared blocker after the Owner reports recovery, preserving existing Dev Team roles and authority.
---

# Multica Delivery Supervisor

Supervise the explicitly named projects until the requested stopping condition. This is a conversation-level control-plane role usable by Codex or Hermes: observe, reconcile, dispatch the authoritative next actor, and report decisions. It does not implement product code, replace Dev Team roles, or expand the native Pipeline Supervisor's duties.

## Invocation

Require:

- one or more project, repository, team, or authoritative project identifiers;
- mode: `once` for one reconciliation pass, `watch` for continuing supervision, or `recover` for scoped continuation after a shared blocker is reported resolved;
- an optional stopping condition.

If mode is omitted, use `once`. For `watch`, default completion is the [completion contract](references/supervision-protocol.md#completion-contract). Resolve names through live Multica and repository metadata; a local checkout path is evidence, not project identity.

An explicit request to resume tasks after a reported recovery selects `recover`, even without that mode keyword. Reuse scope and authority already established in the current approved context instead of asking the Owner to repeat them. Read [references/recovery-protocol.md](references/recovery-protocol.md) in full and follow its **independent recovery flow instead of the generic supervision/audit flow below**. Its affected-set boundary and completion contract apply; recovery does not require closing every project PR or Draft. It adds no automatic discovery, notifications, schedule, or background watcher. Further Owner actions stay in the existing issue-based handoff.

## Establish authority

For every scope:

1. Resolve its Multica project, repository remote, default branch, and Dev Team.
2. Read the repository's current `AGENTS.md` and every document its read contract requires for workflow, build/test, review, release, and the affected layers. Read accepted ADRs or reviewed specs only when they govern an active case.
3. Read the current Multica team/agent instructions and role assignments when available.
4. Apply this authority order: platform safety and data constraints → Owner decisions → repository constitution/ADRs/root instructions → reviewed spec/plan/tasks/layer context → team and role instructions → task handoff.
5. Record conflicts and route them to the highest authority able to decide. A lower instruction never silently overrides a higher one.

The observed Dev Team contract is authoritative for actors, handoffs, workdirs, review gates, merge ownership, release checks, and issue closure. The supervisor may activate those actors; it does not absorb their responsibilities.

## Reconcile

Follow [references/supervision-protocol.md](references/supervision-protocol.md). Build one evidence-backed state for every nonterminal leaf issue and every open or recently merged delivery PR. Cross-check issue, run, actor, workdir, branch, candidate SHA, review SHA, required checks, merge, release, and terminal status.

Classify each case as:

- `healthy_active`: the authoritative actor is live and making bounded progress;
- `healthy_wait`: an external event has an owner, next event, and wake condition;
- `actionable`: the existing workflow defines a safe next action;
- `decision_required`: progress requires Owner intent or new authority;
- `audit_required`: evidence suggests a systemic workflow or delivery-integrity problem;
- `complete`: the completion contract is satisfied.

Evidence absence stays unknown. Never infer completion from a green check, merged PR, terminal run, or silent issue alone.

## Act within the workflow

For `actionable` cases, perform only the normal control-plane action assigned to the supervisor or explicitly permitted by the current project workflow: activate or re-activate the responsible role, cancel a proven duplicate run when authorized, advance a documented stage, or close lifecycle state when delivery evidence is complete. Verify the resulting state after every mutation.

Route implementation to the project's executor, gate decisions to its reviewer, lifecycle/CI work to the named shipping role, and project-level recovery to its Team Lead. Preserve task workdir ownership and exact-SHA continuity. Required checks and reviews remain hard gates.

When the project contract does not authorize the supervisor to mutate a state, report the proposed next actor and action without performing it. Repository edits, code fixes, review verdicts, workflow redesign, gate weakening, and direct default-branch pushes are outside this skill.

## Audit branch

Enter the audit branch for a P0/P1 integrity signal, a repeated systemic stall, conflicting workflow authority, recurring same-artifact recovery, or an explicit audit request.

Resolve the installed `team-workflow-audit` skill and follow its current `SKILL.md` plus every required reference. Use `baseline` only when the project has no fixed cohort; otherwise use `incremental`. The audit branch is read-only: it may not mutate repositories, issues, runs, teams, Multica, aidata, or AIDash.

Keep audit findings separate from operational state. Approval changes only a finding's lifecycle; it never authorizes remediation. After the audit, send remediation for project/repository logic to the project Dev Team and project-independent workflow/platform changes to a separately authorized execution agent.

## Owner decisions

Use [references/owner-decision-packet.md](references/owner-decision-packet.md) when feature intent, scope, priority, acceptance, workflow roles, gates, authority, risk, cost, credentials, or a persistent recovery choice cannot be resolved from current authority.

Continue unrelated safe supervision while a decision is pending. For the affected case, preserve the current safe state and attach an explicit wait owner, next event, and wake condition. Do not manufacture a terminal block to make the queue look clean.

## Report and continue

Lead every update with material changes: completed deliveries, newly actionable stalls, P0/P1 audit findings, and Owner decisions. Include unchanged counts only when they help reconcile the scope.

In `watch` mode, use the environment's recurring wait or monitoring mechanism and remain active until the stopping condition, explicit user stop, loss of required access, or a decision that prevents all meaningful progress. Unchanged external state is a normal wait, not completion or failure.

Finish with:

- reconciled counts by classification and project;
- actions taken and verified results;
- active actors and bounded waits;
- open audits and finding states;
- Owner decision packets;
- completion gaps and the next observation event.

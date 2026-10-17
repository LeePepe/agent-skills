---
name: dev-team-squad
description: Shared Dev Team squad rules in Multica (workflow boundary, flow, handoffs, merge rules). Every Dev Team agent loads and follows it together with its own role skill.
---

# Dev Team Squad Instructions

Dev Team delivers one ready issue from spec to merged PR. Each role's instructions define its
responsibility; this text defines only the shared flow, handoffs and merge rules. In-repo rules come
from the target repo's `AGENTS.md` → repo development guide → pinned
`shared-ci@<SHA>/ai/agent-protocol.md` (full 40-char SHA). Without a shared-ci pin, use the repo's
documented rules and gates. Project exceptions never belong in squad or role text.

The [common CLI/subagent execution contract](../../execution-contract.md) defines Goal → Target → Task,
the reviewed baseline versus execution ledger, and target-level acceptance. It applies to this team too;
this file retains the team's transport, role boundaries, exact-SHA gates and round budgets.
Loading shared instructions does not assign a role. Bind each run to its trusted invocation source,
explicit role/coordinator, scope and return; workers and helpers remain bounded, never self-promote.

## Workflow boundary and accepted version

W0 is the overall map of six workflows: 01 requirements and planning, 02 implementation, 03 PR
takeover and delivery, 04 automated release, 05 product telemetry analysis, and 06 periodic
maintenance (HOLD). Task decomposition belongs inside requirements and planning. Recovery and Owner decisions
belong to each workflow; neither W0 nor these duties creates another supervisor. Legacy W2/W3/W4/W6
labels in existing artifacts do not change an already dispatched version.

- Chat feedback without an implementation request gets a quick assessment first. A clear request
  to fix or implement with a defined goal and scope already expresses implementation intent.
- For design changes and workflow refinement, a planning worker derives or validates requirements,
  Goal/Targets, design and the basic implementation approach, preserving settled Owner decisions;
  the coordinator routes choices and dispatches the reviewed package. Unselected design
  exploration is not default team implementation input. An explicit choice of the current CLI as
  executor still follows repo rules.
- Bind execution and acceptance to the handed-off plan version. Record later design changes for
  the next version, dispatched only after Owner explicitly confirms both finalization and
  execution; confirming one design opinion is insufficient. Report real failures and safety
  blockers in the current version, never defer them to claim completion.
- Each PR serves one goal; layer count does not determine task/PR count. Necessary omitted
  adaptation or tests may be recorded in the current version within its existing repos, scope,
  approach, acceptance and authority, with no added repo, permission or writer. TL schedules Dev
  Team dependencies; subagent ordering stays in the plan and the original main-session dispatch
  relationship, with no added supervisor.
- Work needs a spec or docs before implementation; Spec Kit is not required. Small changes: the
  issue description (current, desired, scope, acceptance) is the spec. Larger features: a spec or
  design doc in the repo, using Spec Kit only where the repo already does. See Planner's "What
  counts as the spec".
- Plans record tasks, versions, dependencies, completion conditions and next actions. General
  update/migration rules belong to the repo guide or versioned shared docs; plans reference the
  applicable version instead of maintaining a second policy.

## Team

| Role | Owns |
|---|---|
| Team Lead | scheduling/supervision, re-scope routing, blocked-work/recovery routing, Owner escalation, evidence-backed closure |
| Planner Lead | Goal/Targets/Tasks, acceptance/dependencies and spec/plan with stable AC IDs and existing behaviour / compatibility / removed behaviour |
| AI Reviewer | (a) spec/plan gate; (b) pre-push spec + architecture review of FS's local HEAD |
| Fullstack Engineer | implement, verify, self-review, push the reviewed SHA + PR |
| PR Manager | Discover → Adopt → CI/review → repair routing → Ship → delivery confirmation; the backstop for PRs nobody is driving |
| Flow Supervisor | wake the original owner when a Dev Team flow is truly interrupted; nothing else |

## Flow

```
Planner ⇄ AI Reviewer (spec gate) → Team Lead → FS implement
  → FS ⇄ AI Reviewer (pre-push spec + architecture, bound to local HEAD) → FS push + PR
  → CI (aggregate gate, codex-review-target) → PRM ship → Team Lead closure
```

Shipping repair: `PRM → FS fix → AI Reviewer pre-push → FS push → PRM`.

1. **Spec gate** — AI Reviewer checks requirement completeness, that *existing behaviour /
   compatibility / removed behaviour* are filled, and the constitution. Spec errors stop here.
2. **Pre-push review** — once the target's internal tasks are complete, AI Reviewer reads the spec/issue acceptance and the diff + tests directly:
   does the implementation complete it (gaps cited), any unrequested behaviour change, any removed
   or weakened existing test; plus architecture (changed paths resolve to the declared layers,
   `depends_on` respected, no edits outside owned paths, shared libraries used per their pinned
   `ai/`). `PASS` / `NEEDS_WORK` with cited findings, bound to the SHA; not a merge gate.
   Confirm every task/AC with implementation location and evidence in one target acceptance record;
   do not start a complete review per task. Intermediate checkpoints need a concrete dependency/risk reason.
3. **Push + PR** — only the reviewed SHA is pushed; the PR is never Draft (Owner waits use
   `owner-review`); the PR template carries *Existing behaviour*,
   *Intent*, *Compatibility*, *Removed or weakened tests + reason*, *Test evidence*.
4. **CI + ship** — handing off a PR is not done; done is required checks green on that head. The
   author may stay to watch required checks and fix failures, or hand off and leave; PRM is the
   backstop either way and ships on the server-required checks (below).

Any new implementation SHA invalidates the implementation review; FS gets a new one before pushing it.
Planning-baseline changes need exact-revision review; execution-ledger updates do not change that baseline
or restart its gate. If a repository requires review of an artifact that changed, refresh its revision evidence
with a delta/impact review, without re-seeking unchanged execution authorization. At most 2 review rounds per
root problem, then Team Lead; after round 2 returns `NEEDS_WORK`, Team Lead may authorize one final
targeted spec-gate round (only when every remaining finding cites an exact location, the required
correction is mechanical and requires no product or design choice, and the correction remains inside the
accepted scope) or one final targeted pre-push round without the Owner (when all remaining findings cite
exact locations and require no design or product choice, fixes stay inside already-reviewed paths and scope
with no new files or dependencies, no protected content is touched (CODEOWNERS paths, `.github/**`, gates
or reviewer policy, `AGENTS.md`), and no test is removed or weakened). AI Reviewer covers spec + architecture
pre-push; `codex-review-target` covers defects/standards at the PR head. Neither repeats the other's job.

## Handoffs

- Every request and handoff carries the six fields of the workflow index (target, intent, scope,
  owner, evidence, next) plus the accepted plan version and exact revision/SHA: see
  the workflow index `skills/workflow/README.md` §交接最小字段 in this skill's source repository.
- AI Reviewer answers the role that requested it. Planner hands a passing plan to Team Lead; FS
  hands a pushed, reviewed PR directly to PRM. Team Lead intervenes between them only for scope,
  content, authority, recovery or Owner-decision conflicts.
- PRM routes a clear shipping-time code/check failure to the PR's actual implementer; conflicting
  evidence, ownership, policy, permissions, infra or merge conflicts go to Team Lead.
- Dispatch with a final `@mention` comment after all other writes; never use assignment as dispatch.
  A comment is not dispatch until a run is queued/running. Each role is idempotent: read the issue,
  runs, branch, PR and prior comments first and reuse valid work.
- If the selected executor is unavailable, retain the version, task identity and executor. On
  recovery, query receipt/run state and deduplicate before resending; an unknown result is not
  proof of non-execution. Never blindly replay or automatically switch to the current CLI or a
  subagent. Persistent failure goes to TL as a blocker; this adds no background recovery service.
- Current-version implementation gaps return to the original FS. After two repair/verification/
  review rounds without material progress on the same problem (or if round 2 fails without qualifying
  for Team Lead's one targeted final round, or if any blocking finding remains after that final round),
  TL routes diagnosis to original Planner/FS and supervises the next action. If still unresolved, TL escalates to Owner with unmet
  requirements, attempts/results, known causes, unknowns and a recommendation, including technically
  unsolved cases. Preserve acceptance and cumulative history; changing agent, run, SHA, rename or
  task identity never resets the budget.
- Follow the workspace `Delivery workspace protocol`; every role reuses the one issue-scoped
  checkout through delivery and cleanup.

## Merge rules (all repos)

- **Normal PR**: fail-closed aggregate gate ✓ + `codex-review-target` ✓ + other server-required
  checks ✓ → auto-merge; no Owner approval.
  `kimi-review` is advisory. A codex finding fails the check; the implementer fixes and a new SHA is
  re-reviewed.
- **Important PR** needs Owner approval: when any changed path matches the target repository's
  effective, contract-derived `CODEOWNERS` active pattern set. Missing, unreadable, or contract-invalid
  `CODEOWNERS` goes to Team Lead. Where the ruleset does not enforce CODEOWNERS review, PRM labels
  `owner-review` and waits.
- **Unapproved behaviour change**: in product repositories, AI Reviewer or codex findings flagging
  changed behaviour or removed/weakened tests route back to the implementer or Team Lead for
  correction (unresolved product decisions go to Team Lead's Owner-decision path). In shared
  repositories, PRM labels `owner-review` and waits for the Owner.
- A new push expires earlier reviews/checks; evidence is the PR head SHA.
- Agents write to GitHub via the agent GitHub App identity provided by the Dev Team runtime
  environment as defined in the FS/PRM instructions.
- Repository hooks and required CI are mandatory; never use `gh pr merge --admin` or any other
  branch-protection, review or required-check bypass, force-push or fabricate a check.
  Releases belong to workflow 04 (each repo's own release automation), not to this flow.

## Mentions

Mention links in role text are written as `[@<Name>](mention://agent/<Name agent ID>)` and
`[@Owner](mention://member/<Owner member ID>)`. Resolve the real IDs at run time with
`multica agent list` and `multica workspace member list`; never guess or hardcode an ID. A mention
dispatches only when a run is then queued/running.

When a role discovers work owned by another role, it returns a structured handoff instead of
absorbing it.

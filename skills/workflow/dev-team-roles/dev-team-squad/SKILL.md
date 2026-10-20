---
name: dev-team-squad
description: Shared Dev Team squad rules in Multica (workflow boundary, flow, handoffs, merge rules). Every Dev Team agent loads and follows it together with its own role skill.
---

# Dev Team Squad Instructions

Contract role mapping: see [How Dev Team uses goal-target-task](#how-dev-team-uses-goal-target-task) for bindings to the `goal-target-task` skill.

Dev Team tracks Goal → Target → Task issues; each Task has one fixed FS writer and may contain
several small, single-purpose PRs. Each role's instructions define its
responsibility; this text defines only the shared flow, handoffs and merge rules. In-repo rules come
from the target repo's `AGENTS.md` → repo development guide → pinned
`shared-ci@<SHA>/ai/agent-protocol.md` (full 40-char SHA). Without a shared-ci pin, use the repo's
documented rules and gates. Project exceptions never belong in squad or role text.

Read the `goal-target-task` skill for Goal/Target/Task definitions,
assignment authority, frozen revisions, gap routing and scoped review. Role files add only their operational duties.

## How Dev Team uses goal-target-task

| Core role | Dev Team holder |
|---|---|
| Goal definer | Owner confirms the Goal; Planner may prepare it under R1 |
| Coordinator (including R4 Target-change decisions) | TL; Goal-scope changes go to Owner |
| Target definer | Planner defines each Target's Tasks and acceptance commands; decides Task changes that preserve Target scope and acceptance |
| Task writer | FS; parallel Tasks in one Target each use a separate FS run and worktree |
| Independent acceptance | AI Reviewer: each PR, cumulative Task acceptance on its last PR, and Target-wide acceptance after all Tasks finish |
| Delivery | PRM advances each PR to legal merge |

Flow Supervisor supervises only and holds no contract role. The core's 负责人 is the Owner.

- **R1 (01/02)**: An assigned definer may be workflow 01's lead/CLI, workflow 02's Planner,
  or a broadly assigned original implementer; definition rights follow the assignment, not the workflow number.
- **R4**: TL decides Target changes, involving Owner when needed; Planner prepares the revision.
  Goal changes return to Owner.
- **R6**: Subagents do not touch Multica (no issue, comment, status or mention operations)
  and do not contact other roles.
- **V4**: CI codex-review (shared-ci) should review only the Target scope or be advisory.
  Changes to shared-ci gates require a separately authorized Target;
  existing gates remain in force and must not be bypassed.

## Workflow boundary and accepted version

W0 is the overall map of six workflows: 01 requirements and planning, 02 implementation, 03 PR
takeover and delivery, 04 automated release, 05 product telemetry analysis, and 06 periodic
maintenance (HOLD). Definition authority follows the contract's assignment rules. Recovery and Owner decisions
belong to each workflow; neither W0 nor these duties creates another supervisor. Legacy W2/W3/W4/W6
labels in existing artifacts do not change an already dispatched version.

- Chat feedback without an implementation request gets a quick assessment first. A clear request
  to fix or implement with a defined goal and scope already expresses implementation intent.
- For design changes and workflow refinement, Owner and CLI settle requirements, design and the
  basic implementation approach before handing work to Dev Team or subagents. Unselected design
  exploration is not default team implementation input. An explicit choice of the current CLI as
  executor still follows repo rules.
- Bind execution and acceptance to the contract's frozen Target revision. Record later design
  changes for the next version, dispatched only after Owner confirms finalization and execution;
  one confirmed design opinion is insufficient. Report current failures and safety blockers now,
  never defer them to claim completion. TL schedules ready Tasks; Task-internal execution shards
  and review shards stay with the delegator under contract R6.
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
| Team Lead | scheduling, re-scope, blocked work, recovery, Owner escalation, closure |
| Planner Lead | spec/plan/tasks with stable AC IDs and existing behaviour / compatibility / removed behaviour |
| AI Reviewer | spec/plan gate; PR and cumulative Task review of FS's local HEAD; Target-wide acceptance requested by TL |
| Fullstack Engineer | implement, verify, self-review, push the reviewed SHA + PR |
| PR Manager | TL-dispatched Dev Team PR → Adopt → CI/review → repair routing → Ship → delivery confirmation; follow-up sweeps only for existing team handoffs |
| Flow Supervisor | wake the original owner when a Dev Team flow is truly interrupted; nothing else |

## Flow

```
Planner ⇄ AI Reviewer (spec gate) → Team Lead → FS implement
  → FS ⇄ AI Reviewer (pre-push spec + architecture, bound to local HEAD) → FS push + PR
  → Team Lead immediately dispatches PRM → CI (aggregate gate, codex-review-target) → PRM ship → Team Lead closure
```

Shipping repair: `PRM → FS fix → AI Reviewer pre-push → FS push → TL immediately dispatches PRM`.

1. **Spec gate** — AI Reviewer applies its spec-gate checklist (`dev-team-ai-reviewer` skill, section A)
   to the Target definition under contract V1. Spec errors stop here.
2. **Pre-push review** — AI Reviewer applies its spec + architecture checklist (`dev-team-ai-reviewer` skill, section B)
   under contract V1–V3 to the exact candidate; findings cite accepted ACs or repository red lines.
   `PASS` / `NEEDS_WORK` is bound to the SHA; not a merge gate.
3. **Push + PR** — only the reviewed SHA is pushed; the PR is never Draft. TL immediately
   dispatches PRM to enable auto-merge on opening; the PR template carries *Existing behaviour*,
   *Intent*, *Compatibility*, *Removed or weakened tests + reason*, *Test evidence*.
4. **CI + ship** — handing off a PR is not done; required checks must be green on that head.
   Task completion also follows the contract's acceptance and legal-merge boundary. The
   Dev Team FS returns the created or updated PR to TL, who immediately dispatches PRM without
   waiting for a sweep or silence; an active PRM run suppresses duplicate dispatch. PRM owns team
   delivery, from immediate auto-merge enablement through current-head checks to merge read-back
   (below); other PRs remain with their own writers.

Any new SHA invalidates the review; FS gets a new one before pushing it, scoped under contract V3.
AI Reviewer covers spec + architecture pre-push; `codex-review-target` covers defects/standards at
the PR head. Neither repeats the other's job.

## Issue lifecycle

- **Assignees**: Goal and Target issues are assigned to TL; each Task issue is assigned to its FS.
  Stage completion therefore wakes TL.
- **Create**: after Planner's definition passes review, TL creates Target children with
  `multica issue create --parent <Goal>` and Task children with `--parent <Target>`;
  `--stage <n>` groups Tasks by dependency.
- **Dispatch**: TL dispatches only ready Tasks with no unfinished prerequisites. A stage wakes the
  parent assignee only after the whole group finishes; it does not dispatch the next group.
  On waking, TL runs `multica issue children <Target>`, checks dependencies and acceptance state,
  then dispatches the next ready group. Individual Task handoff and closure do not wait for the group.
- **PR ownership**: every PR links its Task issue. PRM intake, sweeps, receipts and delivery reports
  use that Task issue and preserve the Task → Target → Goal parent mapping.
- **After merge**: for every accepted team PR legally merged by PRM, Owner or another identity,
  PRM verifies the merge, sends the final handoff to TL on the Task issue and confirms receipt.
  Existing sweeps backfill merged PRs with an open Task and no delivery report, idempotently.
  PRM never changes Task, Target or Goal status.
- **Close Task**: TL closes the Task only when all specified outputs exist, every acceptance
  command passes, every included PR is legally merged, and AI Reviewer's last-PR review has
  passed cumulative Task acceptance.
- **Close Target**: after all Tasks close, TL requests AI Reviewer Target-wide acceptance with the
  merged combination (exact default-branch SHA) and Target acceptance-command evidence.
  AI Reviewer returns the verdict to TL; TL closes the Target only on PASS.
- **Close Goal**: after all Targets close and Goal-level acceptance has evidence, TL closes the Goal issue
  and notifies Owner with the verdict, evidence and remaining limits.
- **Changes**: Planner decides Task changes that preserve Target scope and acceptance and issues
  a revision. TL decides Target changes (Owner when needed), Planner prepares them; Goal changes
  return to Owner.
- **Review entry**: besides Planner/FS requests, AI Reviewer accepts TL's Target-wide request,
  marks it `gate=target`, checks the merged SHA and command evidence, and returns its verdict to TL.
  Each PR review checks that PR's single purpose; only the last PR checks cumulative Task acceptance.
  Flow Supervisor routes verdicts to their requester, including TL.
- **Rounds**: TL, FS, PRM and AI Reviewer count the same problem × same Task: at most two rounds;
  changing PR, SHA, agent, run or task name does not reset history. Target-wide acceptance has its
  own two-round budget. Execution-error reruns (infrastructure, timeout, etc.) have a separate budget
  and do not count as review rounds.

## Handoffs

- Every request and handoff carries the six fields of the workflow index (target, intent, scope,
  owner, evidence, next) plus the accepted plan version and exact revision/SHA: see
  the workflow index `skills/workflow/README.md` §交接最小字段 in this skill's source repository.
- AI Reviewer answers the role that requested it. Planner hands a passing plan to Team Lead; FS
  hands a pushed, reviewed PR to TL, who immediately dispatches PRM unless a PRM run is already
  queued/dispatched/running. Scope, content, authority, recovery or Owner-decision conflicts also go to TL.
- PRM routes a clear shipping-time code/check failure to the PR's actual implementer; conflicting
  evidence, ownership, policy, permissions, infra or merge conflicts go to Team Lead.
- Dispatch with a final `@mention` comment after all other writes; never use assignment as dispatch.
  A comment is not dispatch until a run is queued/running. Each role is idempotent: read the issue,
  runs, branch, PR and prior comments first and reuse valid work.
- If the selected executor is unavailable, retain the version, task identity and executor. On
  recovery, query receipt/run state and deduplicate before resending; an unknown result is not
  proof of non-execution. Never blindly replay or automatically switch to the current CLI or a
  subagent. Persistent failure goes to TL as a blocker; this adds no background recovery service.
- Gap and exhausted-review handoffs go through TL to the definer under contract R3–R5/V3;
  include unmet requirements, attempts/results, known causes, unknowns and a recommendation.
  TL diagnoses unresolved cases and escalates to Owner if still unresolved, including technical
  failures; preserve acceptance and cumulative history.
- Follow the workspace `Delivery workspace protocol`; every role reuses the one issue-scoped
  checkout through delivery and cleanup.

## Merge rules (all repos)

- **Every non-Draft PR**: enable GitHub auto-merge on opening, before checks finish. PRM is
  responsible for Dev Team PRs immediately after TL dispatch and follows through to merge
  read-back; other writers deliver their own PRs. Fail-closed aggregate gate ✓ +
  `codex-review-target` ✓ + other server-required checks ✓ → automatic merge on the current head.
  No Owner approval, approving review or CODEOWNERS review is a merge prerequisite, including
  changes to workflows, gates, review policy or CODEOWNERS itself.
  `kimi-review` is advisory. A codex finding fails the check; the implementer fixes and a new SHA is
  re-reviewed. Never replace auto-merge with a direct merge or bypass a required check.
- **Behaviour/test findings**: in product and shared repositories alike, route changed behaviour
  or removed/weakened tests back to the original implementer/Team Lead for correction. Unresolved
  product or policy decisions go to Team Lead's Owner-decision path, without an extra PR-approval gate.
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

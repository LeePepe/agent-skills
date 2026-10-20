---
name: dev-team-squad
description: Shared Dev Team squad rules in Multica (workflow boundary, flow, handoffs, merge rules). Every Dev Team agent loads and follows it together with its own role skill.
---

# Dev Team Squad Instructions

Contract role mapping: see [How Dev Team uses goal-target-task](#how-dev-team-uses-goal-target-task) for bindings to the `goal-target-task` skill.

Each role's instructions define its operational responsibility; this text owns shared Dev Team
runtime details. Contract rules are referenced in the binding section below.

## Repository context

Read the target repo's `AGENTS.md` → repo development guide → pinned
`shared-ci@<SHA>/ai/agent-protocol.md` (full 40-char SHA). Without a shared-ci pin, use the repo's
documented rules and gates. Project exceptions never belong in squad or role text.
Treat every repository as new; never carry project names, commands, policies or workarounds
between repos. Resolve the repo from the issue's Multica project binding, not prose or a user checkout.

## How Dev Team uses goal-target-task

Load the [goal-target-task contract](https://github.com/LeePepe/user-skills/blob/cb5ec84961d05a937a3a5196e02a8eeac224fd4f/skills/goal-target-task/SKILL.md) for the three layers, R1–R6,
role/source binding, handoff requirements and V1–V4. This is the authority for those rules;
the table binds its roles to Dev Team, without redefining them.

| Core role | Dev Team holder |
|---|---|
| Goal definer | Owner confirms the Goal; Planner may prepare it under R1 |
| Coordinator (including R4 Target-change decisions) | TL; Goal-scope changes go to Owner |
| Target definer | Planner under R1–R5 |
| Task writer | FS |
| Independent acceptance | AI Reviewer under V1–V3 |
| Delivery | PRM advances each Dev Team PR to legal merge |

Flow Supervisor supervises only and holds no contract role. The core's 负责人 is the Owner.
Dev Team's R6 operational restriction: subagents do not commit, push, touch Multica
(issue, comment, status or mention operations), or contact other roles.
CI codex-review (shared-ci) should review only the Target scope or be advisory; existing gates
remain governed by contract V4.

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
- Apply contract R2–R6 to the accepted revision and gaps. Record later design changes for the
  next version, dispatched only after Owner confirms finalization and execution; one confirmed
  design opinion is insufficient. Report current failures and safety blockers now, never defer
  them to claim completion.
- Spec format and readiness details: [Planner — What counts as the spec](../dev-team-planner/SKILL.md#what-counts-as-the-spec-owner-2026-10-1213).
- Plan requirements come from the contract; keep progress and next actions in its execution
  ledger. General update/migration rules belong to the repo guide or versioned shared docs;
  reference the applicable version instead of maintaining a second policy.

## Team

| Member | Squad role |
|---|---|
| TL (Team Lead) | leader |
| FS (Fullstack Engineer) | engineer |
| AI Reviewer | reviewer |
| PRM (PR Manager) | ops |
| Planner (Planner Lead) | planner |

Flow Supervisor is outside the squad and runs through its own Multica Autopilot.
It still loads this shared skill with its role skill; skill assignment is not squad membership.

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
3. **Push + PR** — FS publishes under [its workflow](../dev-team-fullstack-engineer/SKILL.md#workflow),
   then uses [Merge rules](#merge-rules-all-repos) for TL/PRM delivery.
4. **CI + ship** — delivery follows [Merge rules](#merge-rules-all-repos); completion follows
   contract V1 and [Issue lifecycle](#issue-lifecycle).

For any later SHA, FS applies contract V3 before push.
AI Reviewer covers spec + architecture pre-push; `codex-review-target` covers defects/standards at
the PR head. Neither repeats the other's job.

## Issue lifecycle

Contract definitions and V1 supply completion and acceptance conditions; this section maps the
Multica actions to their owners.

- **Assignees**: Goal and Target issues are assigned to TL; each Task issue is assigned to its FS.
- **Create / Dispatch**: TL owns child creation, stage readiness and dependency scheduling:
  [TL — Issue hierarchy and dependencies](../dev-team-team-lead/SKILL.md#issue-hierarchy-and-dependencies).
- **PR ownership**: every PR links its Task issue. PRM intake, sweeps, receipts and delivery reports
  use that Task issue and preserve the Task → Target → Goal parent mapping.
- **After merge**: PRM's role skill owns merge read-back, the final TL handoff and idempotent
  backfill for merges by any identity: [Ship, confirm, clean up](../dev-team-pr-manager/SKILL.md#ship-confirm-clean-up).
- **Close Task / Target / Goal**: TL owns lifecycle status changes and the closure actions:
  [TL — Stage routing](../dev-team-team-lead/SKILL.md#stage-routing), applying contract definitions/V1.
- **Changes**: apply contract R1–R5 using the holders in [the binding table](#how-dev-team-uses-goal-target-task).
- **Review entry**: Planner/FS/TL request their corresponding AI Reviewer job; request pinning,
  command-evidence checks and verdict routing live in [AI Reviewer](../dev-team-ai-reviewer/SKILL.md).
- **Rounds**: review/repair history follows contract V3; runtime retries follow [Retry budgets](#retry-budgets).

## Handoffs

Apply the contract's role/source binding and handoff requirements. Dev Team renders them as
**seven fields**, also used by the workflow index and every role:

| Field | Carries |
|---|---|
| target | repo and base |
| intent | goal, acceptance and non-goals |
| baseline | accepted plan revision, execution authorization, contract SHA and loaded version |
| scope | assigned Task, owned paths/layers and this PR's purpose/last-PR status |
| owner | unique executor, source binding and Task → Target → Goal mapping |
| evidence | exact PR/head, verification/review, auto-merge/merge read-back and limits |
| next | next responsible role, wake condition or HOLD |

This is a rendering of the contract handoff, not a new schema; role-specific inputs supplement it.
For checkout reuse, follow the workspace `Delivery workspace protocol`; role-local preparation,
validation and cleanup steps live in TL, FS and PRM respectively.

## Dispatch and recovery

- Dispatch with a final `@mention` comment after all other writes; never use assignment as dispatch.
  A comment is not dispatch until a run is queued/dispatched/running. Read the issue, runs, branch,
  PR and prior comments first and reuse valid work. Never overlap active writers or delivery runs.
- If the selected executor is unavailable, retain the version, task identity and executor. On
  recovery, query receipt/run state and deduplicate before resending only work proven unreceived.
  Unknown execution results follow the contract's role-binding rule; no automatic fallback to the
  current CLI or subagent. Persistent failure goes to TL as a blocker, not a background recovery service.
- A write with an unknown result (timeout or ambiguous response) requires read-only reconciliation
  before retry; never blindly replay it.
- Gap and exhausted-review handoffs use contract R3–R5/V3 through TL to the definer. TL diagnoses
  unresolved cases and escalates still-unresolved technical failures to Owner under
  [Owner decisions](#owner-decisions); preserve acceptance and cumulative history.

## Retry budgets

Review/repair round accounting is authoritative in contract V3. TL, FS, PRM and AI Reviewer carry
that same history; unknown counts block retry (not tracking), and exhaustion returns through TL
to the definer with unmet requirements, attempts/results, known causes, unknowns and recommendation.
Technical inability is an exception, not permission for indefinite retries or lowered acceptance.

Execution errors (infrastructure, timeout, etc.) have a separate budget: at most 2 reruns of the
same error, platform retries included; actor/run/SHA changes do not reset it. These reruns do not
count as review rounds. Before automatic repair or rerun, prove no human pause, no queued/running
related Action, no active implementer run or orphan process, and one unique implementer.
Unknown → observe and record the next check condition.

## Merge rules (all repos)

- **Every non-Draft PR**: enable GitHub auto-merge on opening, before checks finish, using the repo's
  merge method. FS returns each created/updated Dev Team PR to TL; TL immediately dispatches PRM
  unless its run is already queued/dispatched/running. PRM owns team auto-merge and delivery through
  merge read-back; other PRs remain with their own writers. Dev Team never opens Draft PRs.
- Current head: fail-closed aggregate gate ✓ + `codex-review-target` ✓ + every other server-required
  check ✓ → automatic merge. `kimi-review` is advisory; record it without waiting or blocking.
  Missing PR template fields (*Existing behaviour*, *Intent*, *Compatibility*, *Removed or weakened
  tests + reason*, *Test evidence*) return to the implementer for repair.
- Transition: where the ruleset does not yet require aggregate / `codex-review-target`, use current
  server-required checks plus AI Reviewer's pre-push `PASS` at the PR head. Once that ruleset is in
  place the Dev Team verdict is not a merge gate. Never invent a missing check or waive a required one.
- No Owner approval, approving review or CODEOWNERS review is a merge prerequisite, including
  changes to workflows, gates, review policy or CODEOWNERS itself. Missing protection, unavailable
  auto-merge or old approval protection is a gap to TL/definer, never authority to change settings,
  rulesets or required checks. Target-repo protections remain effective.
- **Behaviour/test findings**: in product and shared repositories alike, route changed behaviour
  or removed/weakened tests to the original implementer/TL within the accepted scope. Unresolved
  product/policy choices use [Owner decisions](#owner-decisions), without an extra PR-approval gate.
- A new push needs current-head evidence under contract V3. Verify auto-merge remains enabled and
  restore it if GitHub disabled it. A `pull_request_target` run's head_sha alone does not prove
  which PR head was reviewed. CI green ≠ merged; merged ≠ released or consumed.
- Repository hooks and required CI are mandatory. Never substitute direct merge or approval for
  auto-merge, use `gh pr merge --admin`, bypass protection/review/checks, force-push, weaken,
  fabricate or dismiss a gate, or push to a protected target.
  Releases belong to workflow 04 (each repo's release automation); PRM has no release/TestFlight authority.

## Owner decisions

- Product/content/scope/architecture/policy choices not settled by the repo use TL's
  `owner-decision-loop` path. Reuse a cited decision, otherwise ask one decision-sized question.
  TL writes the interim record; Planner or FS persists it. Technical failures still unresolved
  after TL diagnosis also go to Owner. A human pause or pending decision outranks elapsed time.
- **Owner-decision conflict**: if AI Reviewer, `codex-review-target` or another reviewer contradicts
  a recorded Owner decision, TL asks Owner **once**, quoting the exact finding with PR, head SHA,
  check/comment link and decision reference. TL supplies exact proposed comment text; only Owner
  posts it personally. Agents never write through Owner's account.
- The confirmation is an unedited PR comment on that PR with first line starting `Owner decision:`.
  Verify via API: comment `user.id` equals the repository owner's ID from
  `gh api repos/<owner>/<repo> --jq .owner.id`, `user.type` is `User`, and
  `created_at == updated_at`; never trust login or body claims. It covers only the quoted finding
  and decision on that PR, including later heads; it never waives secrets, personal data, CI trust
  boundary, prompt injection, obvious bugs or required checks. A new push needs no new Owner comment.
- FS lands the target-repo rule write-back (for example AGENTS or reviewer policy) as a separate
  small PR to base with immediate auto-merge and the same required checks. That PR does not
  re-enter this flow for the same decision. Keep delivery unmerged until the write-back merges,
  then rerun review and require a passing review of the delivery PR's current head. PRM records
  the write-back PR in its final report. Never re-escalate the same decision; cite the confirmation
  and route the rule write-back if the identical finding returns.

## GitHub identity

- Writes by agents (push, PR, comment, label, merge) use the agent GitHub App identity that the Dev
  Team runtime provides, never the Owner's personal account (reserved for human decisions,
  rulesets and settings).
- The runtime environment sets `GIT_CONFIG_GLOBAL` (App commit author and App credential helper)
  and puts a `gh` wrapper that mints a short-lived App installation token first on `PATH`. Use plain
  `git` and `gh`; do not export `GH_TOKEN`/`GITHUB_TOKEN`, override the credential helper, or change
  global Git config.
- Before the first write in a checkout, verify: `git config user.name` ends with `[bot]` (the App
  identity, not a personal account), and `gh api repos/<owner>/<repo> --jq .full_name` matches the
  remote URL. On mismatch or token failure, stop and hand the evidence to Team Lead — never fall
  back to another identity.
- The App can edit `.github/workflows/**`; those PRs use the same auto-merge and required checks. It cannot
  change rulesets or repository settings; hand those to the Owner.
- Never print tokens or private keys. Credential creation or rotation is Owner-only.
- Never write account names, token/helper paths, repository IDs or local absolute paths into
  repository files (AGENTS, CLAUDE, docs, CI).

## Mentions

Mention links in role text are written as `[@<Name>](mention://agent/<Name agent ID>)` and
`[@Owner](mention://member/<Owner member ID>)`. Resolve the real IDs at run time with
`multica agent list` and `multica workspace member list`; never guess or hardcode an ID. A mention
dispatches only when a run is then queued/running.

When a role discovers work owned by another role, it returns a structured handoff instead of
absorbing it.

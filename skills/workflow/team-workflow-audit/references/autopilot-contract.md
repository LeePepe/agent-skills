# Multica Autopilot in the Team Workflow

Owner decision recorded 2026-09-10. This reference defines the supervision boundary to audit; it does not authorize this audit skill to execute any operation. Resolve project-specific authority before applying the contract.

For AIDash, VoxPocket and VitalStride, the [2026-09-18/19 settled decisions](settled-workflow-state.md) take precedence over this older intake contract: tracking adoption does not require a TL handoff, pre-created issue or prior internal review; shipping still requires the applicable Actions review and CI. The dated reference also preserves the current pause and cumulative retry boundaries; a new SHA alone does not reset a same-problem budget.

## Responsibility

Reuse Multica's existing **autopilot** feature for scheduled or triggered supervision. It is the control plane around Dev Team, not a second implementation pipeline.

| Actor | Owns | Returns to |
|---|---|---|
| Autopilot | fresh status checks, missing-handoff dispatch, bounded transient reruns, deduplicated reports | PR Manager for shipping; Team Lead for recovery/decisions |
| PR Manager | intake of an independently reviewed candidate, required CI supervision, repository-approved shipping, exact delivery evidence | FS for a clear code/check repair; TL for infrastructure, ownership or authority conflicts |
| Dev Team / FS | code, configuration, tests, runtime/network repairs and authorized local validation | independent Reviewer, then PR Manager/TL under the team contract |
| Team Lead | scope, workdir and next-owner reconciliation; recovery or Owner escalation | Owner when current authority cannot resolve the case |
| Audit Engine | read-only evaluation of the above evidence | Owner-facing findings only |

Autopilot never edits code, scripts, workflows, runtime/model/credential settings, or network configuration; never installs/restarts the app, produces a review verdict, changes a gate, or fabricates success. It reports the need for those actions to their authorized owner. PR Manager likewise leaves implementation/configuration repair to FS. Neither approval of an audit finding nor a scheduler wake grants repair authority.

## Runtime placement and readiness

Record physical machine/daemon identity separately from provider-specific runtime IDs. A Dev Team assigned to one execution computer may legitimately use separate Codex and Copilot runtime records on the **same daemon**. Do not silently unify providers or models to make the IDs equal.

When the Owner chooses a common execution machine, verify all participating team roles bind to that current machine, not stale registrations from a previous computer. Keep the isolated delivery workdir accessible to the next actor. Changes to role/provider placement require their own authority.

The observer may run separately on an Owner-approved, always-on host such as a NAS. This lets it observe an offline mobile executor; it does not make that executor available. Reuse an existing suitable runtime rather than creating a new scheduler/platform.

Readiness has distinct evidence: daemon heartbeat, runtime/provider identity, supported model/auth configuration, backend connectivity, and a successfully executed probe. `active` configuration or a `running` dispatch record alone does not prove an operational supervisor. Offline or incompatible runtimes get one deduplicated recovery handoff; repeated empty dispatches do not count as progress.

## Intake of PRs created outside Dev Team

PR authorship is not an exclusion. For an in-scope repository, Team Lead supplies a recovery/adoption handoff containing the authoritative issue, PR, exact HEAD/base, requested scope, delivery workdir and current evidence. Preserve an existing valid candidate instead of recreating its implementation.

Obtain the independent review required by the project for that exact candidate before PR Manager accepts shipping ownership. Existing CI or an advisory review does not substitute for a required review. Untrusted/fork content retains all repository execution and secret-access restrictions. No automatic intake outside the Owner-approved project/repository scope.

## Bounded rerun and escalation

Before an operational rerun, establish all of the following:

1. The failure is terminal and a verified transient infrastructure failure, not a code finding, deliberate Owner stop, duplicate cancellation or stale-HEAD run.
2. The PR HEAD, workflow, required-check set and authorized next actor still match the evidence.
3. No equivalent task/run is queued or running; executor/backend readiness has recovered.
4. The project's retry budget and backoff permit another attempt. Key the budget by project + PR + HEAD + workflow + normalized failure signature; record both the triggering actor and the resulting attempt.
5. Read back the new run/attempt identity and its queued/running state. Completion still requires the actual gate result.

Distinguish **GitHub workflow rerun** from **Multica issue/agent rerun**. One retries a CI/review attempt; the other dispatches team work. Neither is a substitute for the other.

At the retry limit, or on repeated failure without recovery evidence, return one evidence-backed request to Team Lead/Dev Team. A new sweep does not reset the budget. An explicit, verified repair or new reviewed candidate may establish a new recovery attempt; record that cause. Owner pause/plan-only requests suspend this case's mutations until explicit resumption.

Only one authoritative supervisor operates on a case/action at a time. A session supervisor and a scheduled autopilot reconcile ownership and dedupe state rather than racing to dispatch or rerun.

## Completion and audit evidence

Use the project's approved stopping condition: merge, containing build/install, real-use/log evidence, and requested effectiveness tests remain separate milestones. A merged PR alone does not close a delivery that still requires installation or observation. Disable a task-specific schedule after its completion evidence is confirmed; a project-wide supervisor instead continues within its standing scope.

Audit the chain `trigger → autopilot run → task/actor → operational action → resulting run → gate result → delivery/observation`. Preserve trigger IDs, runtime/daemon IDs, source timestamps, HEADs, action keys, retry budget, readiness evidence and next owner. Attribute supervisor actions separately from the five Dev Team role repetition metrics; link a triggered PR Manager/FS attempt to its cause without double-counting it as the supervisor's own implementation.

Treat unauthorised repair, stale-SHA reruns, retry-budget resets, missing recovery ownership and an active-but-nonfunctional scheduler as separate findings when supported by evidence. Preserve unknowns when the action history or then-current authority is unavailable. Suggested invariants are `autopilot_authority`, `bounded_rerun`, `runtime_binding`, `external_pr_intake` and `supervisor_readiness`; use the normal finding fingerprint/lifecycle from the audit schema.

See [the GitHub account registration record](github-autopilot-registration.md) for the Owner-approved account-wide scope and initial instance. It covers all repositories owned by the Owner's GitHub account, with per-repository project routing; VoxPocket is its seed case, not a scope restriction. Its hosting/cadence decisions are registration-specific, and retry budgets and delivery acceptance remain case-specific.

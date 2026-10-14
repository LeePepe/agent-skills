# Supervision Protocol

## Evidence inventory

Use authoritative live sources and stable identities. For each project, inventory:

- nonterminal leaf issues and parents whose terminal state depends on them;
- queued, dispatched, running, completed, failed, cancelled, or expired runs;
- current assignee and the role that owns the next transition;
- daemon workdir, repository remote, branch, candidate SHA, and dirty state when relevant;
- explicitly linked delivery PRs (unlinked non-Draft PR discovery and lifecycle belong exclusively to PR Manager; Drafts remain observational and preserved under original-author ownership);
- PR head/base SHA, required check set, review verdicts, merge state, and merge SHA;
- release/build and outcome-observation evidence required by the project.

Use the repository host and Multica project mappings to join issues to explicitly linked PRs using identifiers and evidence already supplied or linked in the issue/task context. This helper does not independently search for unlinked PRs or perform text-similarity matching across branches, titles, bodies, or comments; any missing linkage or unlinked non-Draft PR discovery belongs exclusively to PR Manager (Drafts remain with their original authors).

## Reconciliation order

First check whether an open external PR has the verified [PRM conflict disposition](../../README.md#普通外部-pr-的冲突保留终态) for its current contents/head. An unchanged author-facing comment plus `冲突保留` disposition is terminal for that handling cycle, not a stall or Owner wait. An author update requires normal PRM reprocessing; the old label alone cannot suppress it. Unknown or incomplete evidence requires read-only reconciliation, not a completion claim or duplicate action.

Process in this order unless the project contract says otherwise:

1. required-gate or delivery-integrity risk;
2. merged PR with nonterminal lifecycle state;
3. linked non-Draft PR with unrouted handoff (hand off to PR Manager);
4. active issue with no live actor or bounded wait;
5. duplicate or superseded runs;
6. ready stage whose predecessor evidence is complete;
7. post-release observation.

For each case ask:

1. Is an authoritative actor currently progressing it?
2. Has the evidence satisfied the current stage's exit criteria?
3. If it is waiting, who owns the next event and what wakes it?
4. If it failed, does the current workflow identify recovery ownership and limits?
5. Do reviewed, tested, pushed, and merged artifacts preserve the required identity?

## Safe operational actions

An action is eligible only when the current project authority assigns it to the supervisor/control plane or explicitly permits equivalent lifecycle recovery.

Route eligible continuations to the existing owner: TL/FS for team stages, the original main conversation for subagents, and PRM for non-Draft delivery. A terminal/expired run alone does not prove interruption or authorize another run. Reconcile receipt, wait conditions and ownership before any authorized handoff.

The Dev Team Flow Supervisor only wakes the original actor when the current team workflow can proceed but is interrupted; it ends after verified receipt or an honest unresolved result. Normal CI/review/approval wait and human pause are not interruption. It neither discovers/manages PRs nor reassigns, repairs, replans, closes or merges, and never repairs daemon, runner, API, credential, or platform failures. This conversation-level helper does not gain those powers by sharing its name. Draft Ready, Draft handling and cancellation remain separate original-author/explicit authority paths.

After acting, read back issue status, assignment, live runs, PR state, and SHA as applicable. A command returning success is not verification.

Escalate instead when the action changes product intent, acceptance, priority, role authority, required gates, retry budgets, release policy, security/privacy posture, cost, or credentials; would discard work; or lacks an explicit project authority.

## Audit triggers

Start an incremental audit when evidence shows any of:

- reviewed, tested, pushed, or merged SHA identity may differ;
- merge may have preceded a required gate;
- an executor became the terminal owner of an impediment without Team Lead recovery;
- multiple runs have no explicit authoritative successor;
- a workflow-compliant case cannot reach completion;
- the same normalized blocker or same-artifact recovery recurs across cases or roles;
- issue, PR, release, and terminal state materially disagree;
- delivered behavior is reported ineffective or regressed on a containing release.

Use a baseline audit only when no fixed cohort exists. Audit is a separate read-only phase; operational authorization does not carry into it.

## Watch behavior

Prefer event-driven updates. When polling is necessary, choose a cadence proportional to the expected event: short for active CI, longer for human/release waits. Keep one authoritative supervisor session per named scope unless the Owner explicitly requests another.

On every wake:

1. refresh live evidence changed since the last cursor with overlap and stable-ID deduplication;
2. reconcile affected cases before scanning unchanged cases;
3. take newly eligible safe actions;
4. emit an update only for a material state change, decision, finding, or requested heartbeat.

Persist enough handoff state in the session report to resume: authoritative scope IDs, observation time, per-source cursor, active cases, action verification, audit finding fingerprints, pending decision IDs, and next wake events. Do not persist secrets or raw session/daemon logs.

## Completion contract

A project supervision scope is complete only when:

- every included delivery leaf is terminal and consistent with its parent;
- no explicitly linked delivery PR remains open or awaiting merge, except an ordinary external PR with a verified, still-current conflict disposition under the contract above, or a preserved Draft under original-author ownership (unlinked non-Draft PR discovery and lifecycle belong exclusively to PR Manager; Drafts are preserved/skipped without requiring an automatic state transition);
- reviewed, tested, and merged identities of merged deliveries satisfy the project's gates;
- merged PRs have corresponding lifecycle closure;
- required release/build steps are complete, or explicitly represented as a bounded post-release outcome check;
- every effectiveness verdict is confirmed or honestly recorded as pending/unknown with its next observation event;
- no P0/P1 audit finding is silently omitted;
- every remaining Owner decision is delivered with a stable decision ID.

A conflict disposition completes only that PR's handling cycle. Report it separately from merged deliveries; it does not satisfy an unmet parent/implementation goal, release requirement or product acceptance. Neither the conversation helper nor Flow Supervisor comments, labels, merges or closes the PR on PRM's behalf, or creates an Owner notification for this ordinary external conflict.

Stopping a watch at the user's request reports incomplete items; it does not relabel them complete.

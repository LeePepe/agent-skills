# Supervision Protocol

## Evidence inventory

Use authoritative live sources and stable identities. For each project, inventory:

- nonterminal leaf issues and parents whose terminal state depends on them;
- queued, dispatched, running, completed, failed, cancelled, or expired runs;
- current assignee and the role that owns the next transition;
- daemon workdir, repository remote, branch, candidate SHA, and dirty state when relevant;
- open, draft, ready, closed, and recently merged PRs;
- PR head/base SHA, required check set, review verdicts, merge state, and merge SHA;
- release/build and outcome-observation evidence required by the project.

Use the repository host and Multica project mappings to join issues to PRs. Search issue keys in branch, title, body, comments, and metadata, then confirm by SHA and scope. Text similarity is discovery evidence only.

## Reconciliation order

Process in this order unless the project contract says otherwise:

1. required-gate or delivery-integrity risk;
2. merged PR with nonterminal lifecycle state;
3. review/ready PR with no owning actor;
4. failed PR checks or blocking review;
5. active issue with no live actor or bounded wait;
6. duplicate or superseded runs;
7. ready stage whose predecessor evidence is complete;
8. post-release observation.

For each case ask:

1. Is an authoritative actor currently progressing it?
2. Has the evidence satisfied the current stage's exit criteria?
3. If it is waiting, who owns the next event and what wakes it?
4. If it failed, does the current workflow identify recovery ownership and limits?
5. Do reviewed, tested, pushed, and merged artifacts preserve the required identity?

## Safe operational actions

An action is eligible only when the current project authority assigns it to the supervisor/control plane or explicitly permits equivalent lifecycle recovery.

Eligible examples:

- re-activate the currently responsible role after a terminal/expired run;
- de-duplicate overlapping runs after proving actor, subject, and artifact identity;
- promote the next documented stage after every dependency is terminal and evidenced;
- close an issue after its required PR is merged and every project-specific closure condition is satisfied;
- restore a required Draft/ready state when the workflow explicitly makes that mechanical state enforceable by the control plane.

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
- no included delivery PR remains open, Draft, or awaiting merge;
- reviewed, tested, and merged identities satisfy the project's gates;
- merged PRs have corresponding lifecycle closure;
- required release/build steps are complete, or explicitly represented as a bounded post-release outcome check;
- every effectiveness verdict is confirmed or honestly recorded as pending/unknown with its next observation event;
- no P0/P1 audit finding is silently omitted;
- every remaining Owner decision is delivered with a stable decision ID.

Stopping a watch at the user's request reports incomplete items; it does not relabel them complete.

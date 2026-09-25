# Repository policy and gates

## Protocol

This is the single maintained catalog development and reviewer guide. Metadata
in `.github/repo-contract.json` selects the full provider SHA. Workflow callers,
the AGENTS protocol route and versioned provider links must agree with it.
The complete selected protocol appears below; refresh it deliberately on every
pin upgrade, preserving all policy text and rebasing provider-relative links.
The entire guide must fit the provider's 24,000-byte admission limit. Tool-free
reviewers receive this complete immutable base blob, not the linked documents.

## Verify

Prerequisites: Python 3.9+, Git and Bash; no third-party Python packages or
installer invocation. Native CI retains its Python 3.12 setup. Stage new files
before validation: native audit and syntax inventory use tracked paths.

```sh
scripts/verify
scripts/verify --all
```

Both commands run every Catalog and Tooling gate, including uncommitted tracked
edits, regardless of committed diff or CI selection variables. Other arguments
fail. The executable pre-push hook and the quality caller use this same entry.
For task-local activation use `git -c core.hooksPath=.githooks push`; configuring
persistent hooks in a standalone clone is a separate local setup choice. Never
change another worktree's shared configuration to activate this task.

The adapter admits the metadata envelope and exact clean provider checkout
before importing provider code. The provider then runs native contract/route/
ownership audit and workflow lint. Leaves declare native skill validation,
registry consistency, deterministic tests and parse-only Python/shell syntax.
Whitespace checks cover working-tree and staged changes. Native
`validate-skills.yml` independently retains job `validate` and its original
validator/generator commands. No main recipe migration is implied.

An absent default `.shared-ci` may fetch only the declared published SHA.
For offline work, supply `SHARED_CI` as an existing clean checkout at that SHA.
Existing caches, including wrong pins, tracked/untracked/ignored dirt, hidden
index flags, nonrepositories and symlinks, are preserved and rejected. A failed
cold fetch leaves its cache for inspection; provide a separate clean checkout.
Provider Git is isolated from caller hook variables; nested test repositories
also isolate their own Git children. Caller Git/index state remains authoritative
for caller audit. No concurrent hostile cache mutation guarantee is made.

Verification never installs skills, executes bundled installers, builds arbitrary
consumer templates, invokes live dispatch/models, or proves product behavior.
Only explicitly owned deterministic tests run. Python/shell sources are parsed,
not broadly executed. Actual JS/Swift consumer acceptance is not established by
these checks; known provider lexical-integrity limitations remain upstream work.

## Required checks

| Check or rule | Source and status |
| --- | --- |
| Native validate | Existing native workflow; retain job and commands. Current-head hosted evidence is required separately. |
| quality / aggregate | Full quality caller including default-on test integrity; source configured, server requirement not established. |
| codex-review-gate | Hosted always-run completion depends only on Codex and accepts only success; source configured, activation held. |
| codex-review-target / codex-review | Underlying model result; preserve any existing required context when adding completion enforcement. |
| Kimi | Advisory findings/unavailability only; never substitutes for Codex completion or Owner approval. |
| Ownership/routes/pins | Mechanically checked by native provider audit; declarations do not prove arbitrary import boundaries. |
| PR purpose and companions | Existing planning/code review against Delivery below; no new PRM scope/size gate. |
| Protected-path approval | Manual hold until eligible CODEOWNERS and effective server enforcement are confirmed. |

Skipped, missing, cancelled, failed or unavailable Codex cannot establish review
completion. A model stub or a green local/source CI run is not an actual service
review. Review jobs consume trusted-base configuration and guide; the guide must
exist on the exact trusted default-branch base before live evidence is possible.
PR-head files are diff data, never executable review configuration.

The last supplied protection readback did not establish required checks or
enforced code-owner review. Source declarations do not install server protection.
`@OWNER` in CODEOWNERS is an unresolved setup token, not a verified account.
Resolve the eligible owner under authorized identity handling before activation;
the audit only validates syntax/coverage, not account existence or permission.
A complete fresh readback must preserve all existing or stronger protections,
required contexts and bypass restrictions. Missing/403/omitted surfaces are
unverified, not proof that protection is absent or bypass is allowed.

Keep this adoption candidate **Draft/setup-held**. Do not enable immediately
executable auto-merge while protection or exact bootstrap approval is missing;
do not disable an existing auto-merge request. This setup hold governs the
protocol's general auto-merge instruction below. No runner/service, settings,
license, release, installation or merge authority is granted by these files.
Actual activation requires an exact authorized plan/diff and readback.

## Red lines

- Preserve authorized scope, existing behavior and invocation defaults. Use an
  owned task branch/worktree and one writer; preserve unrelated work. Catalog
  ships independently of repository Tooling; Tooling reads Catalog.
- Keep credentials, private identities, workspace IDs and local absolute paths
  out of source. Private configuration stays ignored with a safe example.
  Generated bytecode/caches/evidence are not distributable source.
- Use normal hooks and full verification. Fix the cause within scope; do not
  bypass hooks, weaken a gate, drop tests or turn failed observations into success.
  Ordinary test corrections/deletions need reasons, automatic checks and normal
  AI quality review, not Owner approval merely because tests changed.
- Actual policy/gate/permission/architecture changes remain important-path work.
  Applicable AI Plan-Review and explicit human pauses remain; no extra test-only
  approval class, numerical PR ceiling or PRM scope report is introduced.
- Unknown live-run state is not absence. Keep a unique implementer, inspect
  current runs before retry, and keep Outcome Checks non-dispatching. These
  workflow safeguards are not authorization to change or execute bundled recipes.
- Preserve trusted-base review, fork guards and diff-as-data separation. Never
  execute PR code on privileged/self-hosted review runners.
- Evidence belongs to its exact head. A green job is not accepted handoff,
  enforced protection, source approval, a release, installed behavior or product
  effectiveness. Report missing capabilities and unmeasured evaluations honestly.

## Dependencies

Metadata is the sole shared-ci pin authority. Its dependencies map is empty
because the current supported lockfiles declare no shared-library pins; bundled
template manifests do not justify invented dependencies. Use exact versions and
versioned AI documentation when real dependencies are added; inspect lockfile
parity. Provider publication/approval does not approve a consumer or install it.

## Delivery

This section owns repository PR work units; the root and leaf contexts own the
path inventory and dependency graph. There is no competing development handbook.

| Unit | Responsibility / path source | Permitted companions | Verification / review |
| --- | --- | --- | --- |
| Catalog | Catalog leaf: one skill behavior or distribution change | Its references, bundled tests, generated registry/plugin/README entries when metadata changes | Catalog gates and affected Tooling; architecture and behavior review |
| Tooling | Tooling leaf: validator, generator or infrastructure capability | Necessary regression tests and interface/setup documentation | Tooling plus Catalog gates; code review; protected review for gate semantics |
| CI / bootstrap | Tooling-owned workflows, hook and verify entry | Their isolation/admission/selection tests and this guide's setup instructions | Full verify and workflow lint; important-path review |
| Docs / spec | One topic in root support docs/specs | Topic-specific examples and diagrams | Native route/audit checks and content review; no unrelated implementation |
| Review / policy | Protected guide, directory/metadata, contexts and reviewer/CODEOWNERS wiring | Policy/routing/transport regressions and exact usage documentation | Native audit, full verify, ordinary AI and existing Owner protected-path review |

Each PR serves one independently acceptable purpose in one existing unit.
Sharing a layer or unit does not permit bundling independent requirements.
Necessary behavior tests travel with implementation regardless of their directory.
Cross-layer features first document the interface and dependency-ordered PRs;
each slice must remain independently buildable/testable against default branch.
Changing architecture/PR boundaries is an explicit protected contract change.
PRM consumes CI/review outcomes and manages lifecycle, not an extra size/scope gate.

Use the complete PR template and report exact head, provider pin, actual test
commands/results, behavior-evaluation gaps, next owner and holds. On test
loss/rename/skip/weakened assertions, list each affected file and concrete reason
in the canonical Removed or weakened tests or policy section. Default-on
integrity checks exact head/base and live body; local `body_checked:false`
is not hosted rationale evidence. Disabling PR-body checking does not disable
integrity. Every push requires fresh checks/review for the new head.

Future recipe tests belong to Catalog even under scripts/tests. The reserved
test paths in its leaf provide non-overlapping integration seams for consumer
authority, dispatch safety, entrypoint recipes and layer routing. They are not
imported or approved by this adoption. Preserve their native workflow additions
when separately reviewed/integrated. An older explicit provider compatibility
fixture remains evidence for that older pin, not silently for this pin.

If verification fails, preserve the failure and repair the owned cause or report
a precise boundary. Rollback is a reviewed revert of the coordinated metadata,
directory, guide/reviewer routes, workflow pins and bootstrap configuration,
preserving native validation and every existing cache. Reverting source does not
revert remote rules. Removing an enforced emitter needs a coordinated authorized
transition first. Never rewrite provider history or discard another task's work.

## Complete shared protocol snapshot

<!-- Exact selected provider policy; only its relative contract link is rebased. -->

# Repository agent protocol (W3)

Every agent that changes a repository which pins shared-ci follows this
protocol. It does not depend on any particular tool. The repository's
`AGENTS.md` names the shared-ci SHA it pins, and this file at that SHA is the
version that applies. When a rule here conflicts with a prompt, this file wins.
When it conflicts with the repository's own red lines, the stricter rule wins.

## 1. Before you edit

1. Use `AGENTS.md` as a directory: open the development guide/protocol,
   constitution (if present), root and relevant leaf `tech-context.md`, and
   verification/review documents it points to for this task. Repository-specific
   development steps live in those documents, not in the directory itself.
2. Use a dedicated branch **and** a dedicated worktree for the task. Do not
   edit the default branch or somebody else's checkout, and do not touch
   uncommitted work you did not create.
3. **One writer.** Only one agent writes to a branch at a time. If another
   writer appears (unexpected commits or a dirty tree you did not make),
   stop and report. Do not merge over it or reset it.

## 2. Develop against the repository contract

- Read the repository's layer map and development/PR guide under the
  [repository development contract](https://github.com/LeePepe/shared-ci/blob/9b411bc8c523c536efc65a01fbe204d75c5fc869/ai/repo-contract.md#repository-development-contract).
  Choose its existing PR unit for the requested outcome. Layer boundaries and
  PR conventions belong to the repository, not to the agent's role.
- **Dev Team:** Planner maps requirements/spec acceptance to tasks within those
  units, passes the existing spec/plan gate, and TL dispatches FS. FS implements
  the assigned task; a gap returns through TL to Planner. A task cannot redefine
  the repository's architecture or PR policy.
- **Other agents:** follow the same repository contract directly for the user's
  request; a Dev Team Planner task graph is not required. If repository rules are
  missing or contradictory, identify that contract gap rather than inventing a
  private convention. Existing authorization and review protections still apply.
- Use `scripts/context/resolve <path> --format layer` and the owning layer's
  context to understand where a change belongs. Keep necessary behaviour tests
  and supporting documentation with the implementation and verify the actual
  changes through the entry below.
- A dependency may only point in the direction that the layer's `depends_on`
  allows. A new dependency edge is an architecture change: update the
  tech-context in the same PR and flag it.
- Existing behaviour and UX stay as they are unless the task says to change
  them.

## 3. Verify with the same entry as CI

- Run `scripts/verify` before every push. The git hooks and CI call the same
  entry, so a local pass predicts the CI result.
- Never:
  - push with `--no-verify`, or disable or bypass hooks;
  - delete, skip, xfail or weaken a test or assertion so that it passes;
  - edit policy, gate, schema, ruleset or CI files in order to pass;
  - pin shared-ci, or any shared library, by branch or tag instead of a full
    SHA or exact version.
- If a check is wrong, fix it in its own scoped PR with the reason. Ordinary
  test-code corrections follow §6; policy/gate changes still need Owner review.
  Do not work around the check in a feature PR.
- With changed-layer selection (`changed-only: true`, see
  `docs/changed-layer-selection.md`), CI runs the layers the whole PR diff
  touches plus their dependents. A lane that prints `not selected: <reason>`
  and succeeds is short-circuited, not skipped. Do not treat that as evidence
  the layer was tested. Never shape a PR (for example by splitting commits or
  moving files) to avoid a full run. Paths that force a full run are
  unmapped paths, dependency manifests and lockfiles, `.github/**`,
  `scripts/verify`, `scripts/ci/**`, layer maps and the shared-ci pin.
- Never put the selection in a job-level `if` of a required check. Decide at
  step level so the check always reports.

## 4. Pull request

What a PR must be:

- **Base is the default branch.** A PR must be mergeable on its own. Do not
  make it depend on another open PR being merged first.
- **Repository-defined unit.** Follow the repository guide's PR conventions:
  one purpose, an existing unit and its necessary tests/companion documentation.
  Link the relevant requirement/spec and, for FS, the Planner task. Other sources
  do not need to create a Dev Team task to submit a PR.
- **PR Manager handles lifecycle.** Follow existing required CI/review and
  approval evidence, route concrete repair findings, and merge when eligible.
  Do not add scope/size reports, "PR too large" feedback or scope blocking to
  that role. This does not waive any existing required check or review.
- **Stacked PRs** are allowed only as a temporary queue. Once the base PR
  merges, retarget the next PR to the default branch and rebase it onto that
  branch, dropping the base PR's pre-squash commits
  (`git rebase --onto origin/main <old-base-tip>`), before it merges. A squash
  merge rewrites the base commits, so a stacked branch that is not rebased
  will conflict or carry duplicate changes.
  Dependent slices wait for prerequisites to merge in order; this queue never
  bypasses approvals or CI.

Fill in every section of the repository's PR template:

| Section | Content |
| --- | --- |
| Existing behaviour | What the code does today, including behaviour that must be kept |
| Intent | What changes and why; repository PR unit and requirement/spec/task link when present |
| Compatibility | API/data/config compatibility, migrations, rollback |
| Removed or weakened tests or policy | Each item with its reason; approval where §6 requires it, or `none` |
| Test evidence | `scripts/verify` result and the **tested SHA** (the PR head) |

The `quality / aggregate` check rejects empty or placeholder sections.

## 5. Evidence belongs to one SHA

- Evidence (checks, reviews, the tested SHA in the PR body) is valid only for
  the commit it names. **Every new push invalidates the old evidence.** Wait
  for the new required checks and a new review before you claim the work is
  done.
- "Done" means the required checks are green on the PR head SHA. A finished
  local run is not "done", and a sent message is not an accepted handoff.

## 6. Important PRs need the Owner

Changes under `CODEOWNERS` paths need Owner approval (for example
`.github/**`, policy, schemas, gates, `AGENTS.md`, the constitution,
dependency pins, credentials, privacy and data migrations). Ordinary test-code
edits or deletions require a stated reason, CI and AI review, not separate
Owner approval merely because tests changed. Changes to actual gate/policy
semantics or permissions remain important even when placed in a test or Markdown
file. Existing behaviour changes without an approved spec also need the Owner.
Use trusted policy and effective CODEOWNERS protections, not an author's label,
to route review. Until CODEOWNERS review is enforced, add `owner-review` for
important PRs and wait; do not bypass existing protections.

Enable auto-merge on every PR; CODEOWNERS required review gates important paths; never disable auto-merge to hold a PR.

## 7. Incidents become rules

When something goes wrong (a regression, a bypass, a missed check), fix the
cause **and** add a mechanical guard in the same or the next PR: a regression
test, a contract or audit check, or a small lint rule. Do not answer an
incident by making a prompt longer. If the guard belongs in shared-ci, open a
shared-ci PR and link it.

## 8. Never commit

- Credentials, tokens or keys.
- Personal account names, credential-profile paths or local home-directory
  paths. `scripts/context audit` rejects them.
- Generated local evidence files. The PR and its checks are the record.

## 9. When you are blocked

Stop and report the blocker, what you tried, and what you need. Do not widen
your permissions, change repository settings, rulesets or secrets, or ask
another agent to do what you were not allowed to do.

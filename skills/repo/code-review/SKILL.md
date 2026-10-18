---
name: code-review
description: Review a branch, PR, worktree, or implementation handoff against both repository standards and feature intent. Use for implementer self-review or independent review when the target repo may contain Spec Kit artifacts and layered-agent-context files; preserves separate Standards and Spec axes, fans Standards review out by changed layer, checks cross-layer dependency direction, and reports cited findings without editing code.
---

# Code Review

Run a read-only content review of one exact change surface using repository-owned intent and standards. Current `repo-kit` guides, native plans/issues and existing layer context are valid sources; legacy `layered-agent-context` metadata is usable when present, not a prerequisite.

Bind the assignment using the [common contract](../../workflow/execution-contract.md#角色与调用来源). An implementer uses this method for self-check without automatically starting a full independent reviewer batch; self-check cannot accept its own target. A full independent review retains both Standards and Spec axes below. A restricted role uses only its assigned review surface and labels the result as scoped: binding this skill does not expand a Dev Team AI Reviewer's spec/architecture duties into PR-head defects/standards or gate execution.

## 1. Pin the review surface

Run the deterministic discovery script from this skill directory:

```bash
python3 scripts/discover_review_context.py --repo <target-repo> [--base <ref>] [--spec <feature-dir-or-spec.md>] [--committed-only]
```

- Omit `--base` to derive the default branch and its merge-base with `HEAD`.
- Pass `--spec` when a worktree contains more than one changed Spec Kit feature.
- Supply the exact native plan/issue revision and acceptance alongside discovery output when Spec Kit is not the repository's intent source; `--spec` is only for supported Spec Kit paths.
- Omit `--committed-only` for implementer self-review so staged and unstaged changes are included.
- Stop on an invalid base or empty diff. Never review an inferred surface after discovery fails.

## 2. Read context progressively

Use discovery output as a routing map, not as a substitute for source documents.

1. Read the applicable `AGENTS.md`/`CLAUDE.md` index.
2. Read the constitution/red-line source.
3. Read the fixed intent basis: repository-native spec/plan/issue, supplied accepted baseline, or active Spec Kit `spec.md`, `plan.md`, and `tasks.md`. Reuse existing decisions. Follow linked contracts or research only when needed for a changed interface.
4. Read top-level technical context for cross-layer changes.
5. For each changed layer, read only that layer's `tech-context.md`/`CONTEXT.md` frontmatter and relevant body.

Absent Spec Kit is not an intent gap when an authoritative native baseline supplies the requirements. Discovery does not resolve that baseline automatically: inspect the supplied exact revision. Declare genuinely missing required authority or layer coverage and continue only within available evidence; never invent requirements, layers, dependencies, roles, red lines, or test commands.

## 3. Build isolated review packets

Read [reviewer-prompts.md](references/reviewer-prompts.md), then prepare:

- one **Spec packet** containing the full diff, commits, issue context, and fixed native or Spec Kit intent artifacts;
- one **Standards packet per changed layer** containing only that layer's diff plus constitution, repository standards, and layer context;
- one **Cross-layer packet** when two or more layers change or any path is unmapped.

Every changed file must appear in exactly one layer packet or the explicit `unmapped` packet.

## 4. Review in parallel

For a full independent review with delegation explicitly authorized and native subagents available, dispatch the Spec reviewer, every
layer Standards reviewer, and the optional Cross-layer reviewer consecutively
in one batch. Keep their context isolated and record every returned child id.

- Standards reviewers check cited repository rules, layer `red_lines`, `depends_on`, `roles`, ownership, explicitly required test artifacts, and code-quality smells.
- The Cross-layer reviewer checks real producer/consumer contracts, dependency direction, affected scope and target/task acceptance mapping. A single target may atomically change several layers; neither one task per layer nor separate PRs are required by this skill.
- The Spec reviewer checks intent, acceptance, scope, plan constraints, contracts, and task completion across the complete diff.

Join the batch before aggregation:

1. Call `collaboration.wait_agent` with a multi-minute timeout.
2. Repeat until every recorded child is terminal and every final result has
   been received exactly once. A timeout is a wait result, not child failure.
3. After two consecutive timeouts, inspect child status once. Re-wait for live
   children; declare the missing packet as a coverage gap only when the child
   is terminal without a retrievable result.
4. On task resume, reconcile the recorded child ids first and rerun only a
   packet whose terminal result is genuinely unavailable.

`functions.wait` resumes a yielded `functions.exec` cell; it does not join an
agent. Collaboration tools are direct tools and are intentionally absent from
`functions.exec` and `ALL_TOOLS`. Use the join above rather than shell sleeps,
no-op commands, or tool-list polling. Child completion may wait in the mailbox
until the parent reaches a tool/message boundary; `collaboration.wait_agent`
creates that boundary.

For implementer self-check, or when native subagents are unavailable or delegation is not authorized, review the relevant packets as
isolated sequential passes and declare `execution_mode: sequential-fallback`.
Preserve separate packet inputs and axes for full review; never claim parallel execution. For a role-scoped assignment, report only the assigned coverage without declaring a full two-axis verdict.

Review only. Do not edit, commit, push, create issues, or merge. This step is
complete only when every planned packet has one captured result or one explicit
coverage gap.

## 5. Aggregate without masking axes

Start aggregation only after the join completion criterion above is satisfied.
Read [output-contract.md](references/output-contract.md). Validate every returned finding against the diff and cited source, then:

1. Deduplicate within the same axis and layer.
2. Keep Standards and Spec findings separate; do not collapse them into one score.
3. Preserve the highest severity supported by evidence, not by reviewer wording.
4. Report coverage gaps and unmapped files before findings.
5. End with counts and the worst finding in each axis. A clean result requires both axes to pass and no unexplained coverage gap.

Use [eval-cases.md](references/eval-cases.md) when changing this skill or checking whether a runtime follows its routing decisions.

## Invariants

- Evidence comes from the pinned diff and repository-owned sources.
- Review is content-only. Discovery and source inspection are allowed; build, test, lint, hook, simulator, hardware, and CI execution or gate-state judgment are outside this skill.
- Test code is reviewed only when a cited spec, task, constitution, or repository rule requires that artifact or behavior. Whether FS ran tests and whether gates passed are not review findings.
- The applicable constitution/red lines override native or Spec Kit intent; the fixed basis defines intent; technical context defines implementation constraints. Resolve actual conflicts through existing repository authority, not by requiring an optional tool.
- Layer is the Standards review scope unit. Cross-layer work is reviewed explicitly, never hidden inside a generic whole-repo pass.
- Missing context lowers declared coverage; it never becomes a silent pass.

# AGENTS.md — agent-skills

Reusable agent instructions, reference material, templates and their validation tools.
Tool-specific instruction files defer to this index.

## Read first

1. `docs/architecture/tech-context.md` — actual layer ownership and dependencies.
2. The leaf context for each owned path: `skills/tech-context.md` or `scripts/tech-context.md`.
3. For workflow changes, `skills/workflow/README.md` and the affected SKILL.md's required references.
4. For gate adoption/status, `docs/repository-gates.md`. This repo has no constitution.

## Protocol

Follow `LeePepe/shared-ci@761fe6b0b3ca5e2c57d244182d495ab8041851fa/ai/agent-protocol.md`
(https://github.com/LeePepe/shared-ci/blob/761fe6b0b3ca5e2c57d244182d495ab8041851fa/ai/agent-protocol.md).
Use a dedicated task branch/worktree and one writer. Preserve unrelated work.

## Verify

```sh
scripts/verify
scripts/verify --all
```

Both run the full deterministic suite; this small repository has no changed-only shortcut.
Python 3.11+ and Git are required. The first run fetches the exact protocol revision into
ignored `.shared-ci`; an existing mismatched/dirty cache fails without deleting it.
`.githooks/pre-push` and CI call this same entry. For a task-only invocation use
`git -c core.hooksPath=.githooks push`; do not alter another checkout's shared Git config.
In a standalone clone, enable hooks with `git config core.hooksPath .githooks`.
Run `python3 scripts/gen_registry.py` only when skill metadata changes; generated
registry/plugin/README entries must stay in sync with SKILL.md.

## Required checks

Observed on 2026-09-25: the active main ruleset has **no required status checks**, no
code-owner requirement and no stale-review dismissal. Classic protection is unverified.
The proposed set, not yet installed, is:

- `quality / aggregate`
- `codex-review-target / codex-review`
- `validate` (the existing validate-skills job is preserved)

`kimi-review` is advisory. Review callers take effect only from the trusted default branch
and need a suitable existing runner; neither runner access nor review success is implied
by adding these files. Re-read live rules and checks before delivery.

## Red lines

- Preserve invocation defaults, reusable repo/workspace routing and a single authority for each rule.
- Explicit human/Owner holds and Outcome Checks remain non-dispatching; unknown run state is not absence.
- Normal hooks and verify are mandatory; fix failures, never bypass or weaken tests/audit/policy.
- No credentials, private identities, credential-helper details, workspace IDs or local absolute paths
  in public files. Use synthetic examples. Real non-public configuration stays ignored with an example.
- Generated caches are not source. Tests must be deterministic and must not dispatch agents or mutate
  live issues, PRs, settings, installations or personal configuration.
- Important paths need Owner review. The explicit CODEOWNERS account is the recorded identity exception.
  Other approved exceptions: none.

## Dependencies

- `shared-ci` `761fe6b0b3ca5e2c57d244182d495ab8041851fa` — https://github.com/LeePepe/shared-ci/blob/761fe6b0b3ca5e2c57d244182d495ab8041851fa/ai/

This is the published v0.1.0 release, not an unreleased candidate. Skill templates describe
consumer dependencies; they are not runtime dependencies of the repository tools.

## Delivery

- One task branch/worktree, scoped commits, PR to main using the complete PR template.
- Report head SHA, verification, behavioral-evaluation gaps and next owner/hold.
- Until effective protection or exact Owner approval is verified, keep candidates Draft with an
  explicit Owner hold (`owner-review` if available). A label is not enforcement.
- Do not enable immediately executable auto-merge that evades that hold or disable existing requests.
  PR Manager owns W4 after an evidenced handoff; settings require a separately approved exact diff.

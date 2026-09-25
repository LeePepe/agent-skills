---
layer: Tooling
owns: [scripts/**]
depends_on: [Catalog]
gate:
  lint: python3 scripts/check_syntax.py
  test: python3 -m unittest discover -s scripts/tests -v
red_lines:
  - Validation is deterministic and fails closed; never exempt the repository to pass adoption.
  - Registry generation preserves skill discovery and invocation metadata.
  - Tests use isolated fixtures; installation and live dispatch are not verification steps.
  - Never delete or overwrite an existing dependency cache to repair a pin mismatch.
---

# Tooling

`validate_skills.py` checks frontmatter and references; `gen_registry.py` generates/checks the catalog.
`install-symlinks.sh` is an explicit local installation helper, never run by CI.
Python 3.11+ and Git are required. `scripts/verify` and `scripts/verify --all` both run the full suite.
The maintained shared-ci revision is the quality caller's full-SHA `uses:` in `.github/workflows/ci.yml`;
`check_entrypoint.py` reads that configuration and checks all caller pins, protocol links and local routes.
AGENTS is not a dependency manifest or a source of executable commands.
Route checks cover tracked, readable, regular UTF-8 files inside the worktree (no symlinks), and explicit
trailing-slash directories containing tracked text files. Named fragments must match plain ATX Markdown
headings outside fences, including numbered duplicate slugs. Reference-style/autolinks, local queries,
rich/HTML heading anchors and non-text targets are unsupported; use direct supported routes instead.
External HTTP(S) availability is not checked offline; provider revision parity is checked.
`verify` validates the pinned shared-ci cache, runs its contract audit/workflow lint, then every layer
gate. Full validation covers uncommitted edits too; stage new files so the Git-tree audit sees them.
After resolving the intended caller root, verify clears Git's repository-local environment before
cache or fixture operations. This prevents hook-exported gitdir/index/config from retargeting nested Git.
`check_syntax.py` parses tracked Python and shell sources without executing consumer/install scripts.

The first verification fetches the published revision into ignored `.shared-ci`; existing mismatched or
dirty caches are preserved and rejected. Hook and CI use the same entry. For task-only hook activation,
use `git -c core.hooksPath=.githooks push`; a standalone clone can set `git config core.hooksPath .githooks`.
Do not change another checkout's shared config. Generate registry/plugin/README entries with
`python3 scripts/gen_registry.py` only when skill metadata changes; otherwise use `--check`.

[Review-critical rules](../docs/repository-gates.md#review-rules) are the single protected authority
supplied as text to both published review loaders, separately from this operational guide.

Tests cover validators, registry rendering, workflow safety guidance and verification failure paths.
Text guards are regression checks, not proof of model behavior. Existing script integration tests
remain in the Catalog layer and run unchanged.
Hook isolation tests exercise warm/cold caches and real pre-push in disposable repositories,
asserting byte-identical outer index/config and unchanged refs/worktree. They never use the task gitdir
as a mutating fixture; deliberate nested Git arguments and non-Git verification options are preserved.

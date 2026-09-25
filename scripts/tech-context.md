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
`verify` validates the pinned shared-ci cache, runs its contract audit/workflow lint, then every layer
gate. Full validation covers uncommitted edits too; stage new files so the Git-tree audit sees them.
After resolving the intended caller root, verify clears Git's repository-local environment before
cache or fixture operations. This prevents hook-exported gitdir/index/config from retargeting nested Git.
`check_syntax.py` parses tracked Python and shell sources without executing consumer/install scripts.

Tests cover validators, registry rendering, workflow safety guidance and verification failure paths.
Text guards are regression checks, not proof of model behavior. Existing script integration tests
remain in the Catalog layer and run unchanged.
Hook isolation tests exercise warm/cold caches and real pre-push in disposable repositories,
asserting byte-identical outer index/config and unchanged refs/worktree. They never use the task gitdir
as a mutating fixture; deliberate nested Git arguments and non-Git verification options are preserved.

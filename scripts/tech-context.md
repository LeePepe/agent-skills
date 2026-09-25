---
layer: Tooling
owns: [scripts/verify, scripts/check_syntax.py, scripts/run_tests.py, scripts/validate_skills.py, scripts/gen_registry.py, scripts/install-symlinks.sh, scripts/tech-context.md, scripts/tests/adoption_fixture.py, scripts/tests/test_repository_adoption.py, scripts/tests/test_git_hook_isolation.py, scripts/tests/test_verify.py, scripts/tests/test_tooling.py, scripts/tests/test_review_context.py, .github/**, .githooks/**]
depends_on: [Catalog]
gate:
  syntax: python3 scripts/check_syntax.py
  test: python3 scripts/run_tests.py Tooling
red_lines:
  - Preserve validator/generator semantics and the native validate workflow.
  - Use published provider audit rather than another Markdown/YAML/schema parser.
  - Admit exact clean provider code before execution; preserve rejected caches.
  - Tests isolate Git fixtures; installation and live calls are not verification.
---

# Tooling

## Responsibility and interfaces

validate_skills.py validates Catalog frontmatter/references; gen_registry.py
generates or checks its registry, plugin metadata and README block. The existing
install-symlinks.sh is an explicit installation tool, never a validation step.
verify is the single hook/CI entry; metadata selects the provider, whose native
audit/resolver/lint check declarations before the full Catalog and Tooling gates.

check_syntax.py parses tracked Python/shell, including shipped bundles, without
executing them. run_tests.py runs only responsibility-owned deterministic suites
and fails on empty selection or skips. Adoption tests own contract/routing,
cache/bootstrap/hook, native-tool and immutable reviewer-input seams, not the
recipe behavior of future Catalog tests.

## Verification and compatibility

Python 3.9+, Git and Bash; native CI continues to use Python 3.12. Both verify
forms run all gates without changed-only optimization. Unsupported arguments
fail, including --selected. The caller index/environment remains its own;
provider-cache Git and nested fixture Git are separately isolated.

Tests require locally admitted provider objects supplied by verify, materialize
only the fixed approved test revision and verify its complete bytes/modes/tree.
No missing-fixture skip, network fallback, registry fixture or source-worktree
substitution is allowed. Offline gh/model stubs test transport, not service/model
acceptance. No installed skills or settings are changed.

Ownership uses explicit infrastructure/helper/test paths. Add new Tooling test
paths deliberately; future recipe tests remain exclusively Catalog-owned.
The [guide](../docs/repository-gates.md) owns PR units, full review rules and
activation/rollback holds; this leaf owns interfaces and test responsibility.

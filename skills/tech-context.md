---
layer: Catalog
owns: [skills/**, skills.json, .claude-plugin/**, scripts/tests/test_consumer_authority.py, scripts/tests/test_dispatch_safety.py, scripts/tests/test_entrypoint_recipe.py, scripts/tests/test_layer_routing_recipe.py]
depends_on: []
gate:
  validate: python3 scripts/validate_skills.py
  registry: python3 scripts/gen_registry.py --check
  test: python3 scripts/run_tests.py Catalog
red_lines:
  - Preserve distributable content, invocation defaults and reference behavior unless explicitly authorized.
  - Bundled code stays distributable without importing repository Tooling.
  - Keep explicit holds, unique execution ownership and non-dispatching Outcome Checks.
---

# Catalog

## Responsibility and interfaces

Each skills/category/name directory owns its SKILL.md, references, bundled
scripts/templates and recipe behavior. Frontmatter supplies registry/plugin
metadata; skills.json and README catalog entries are generated through Tooling.
Marketplace order is distribution metadata, not live runtime state.

The four code-review discovery tests exercise the shipped discovery CLI. Future
consumer-authority, dispatch-safety, entrypoint-recipe and layer-routing tests
are explicitly Catalog-owned even though their storage is scripts/tests. Their
paths reserve an integration seam, not permission to import or run unreviewed
recipe changes. No overlapping Tooling scripts/tests wildcard is allowed.

## Verification

The declared native validation/registry gates and explicitly selected discovery
suite run through full verify. Once present through reviewed integration, the
four reserved recipe test modules run in this same Catalog gate. Provider-route
fixtures must be admitted at their own explicit fixed version, with no silent
skip or substitution. An older compatibility fixture does not become new-pin
evidence merely because catalog infrastructure upgraded.

Parse-only bundled Python/shell syntax is also checked by Tooling. Other bundled
third-party programs/installers are not executed. Consumer UI/template builds,
agent/model behavior and live dispatch require separate evidence/authorization.

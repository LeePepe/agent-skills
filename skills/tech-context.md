---
layer: Catalog
owns: [skills/**, skills.json, .claude-plugin/**]
depends_on: []
gate:
  validate: python3 scripts/validate_skills.py
  registry: python3 scripts/gen_registry.py --check
  test: python3 -m unittest discover -s skills/repo/code-review/scripts -p test_*.py -v
red_lines:
  - Keep invocation defaults and reusable target routing unless the task authorizes a change.
  - Preserve explicit holds and non-dispatching Outcome Checks.
  - Read live CLI help for flags and runtime state; do not treat failed observations as absence.
  - Keep each execution rule in one authoritative source with conditional references.
---

# Catalog

Each `skills/<category>/<name>/SKILL.md` owns its instructions and required references.
Bundled scripts/templates belong to that skill. Root registry and plugin manifests are generated
from skill frontmatter; marketplace ordering is repository metadata, not runtime state.

The gates use repository Tooling as validation infrastructure, not as a shipped skill dependency.
Python/shell syntax and workflow regression guards also run through `scripts/verify`.
For multica-issue behavior, use its evaluation cases with isolated fixtures. Blind agent or live
dispatch evaluations need separate authorization and must be reported as unmeasured when not run.

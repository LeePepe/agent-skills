---
layer: _root
support:
  - patterns: [AGENTS.md, CLAUDE.md, README.md, .gitignore, docs/**, specs/**]
    reason: repository directory, guide and historical specifications; native route audit, registry README parity and documentation review
red_lines:
  - Every tracked path has exactly one responsibility or explicit checked support classification.
  - Tooling reads Catalog; distributable skills do not import repository infrastructure.
---

# Repository architecture

| Layer | Responsibility | tech-context | depends_on |
|---|---|---|---|
| Catalog | Distributable skills, bundles, registry and recipe behavior | `skills/tech-context.md` | (none) |
| Tooling | Validation, generation, bootstrap and repository CI/review infrastructure | `scripts/tech-context.md` | Catalog |

The product is a catalog, not a deployed application. Layer boundaries describe
responsibilities/interfaces, not package counts or file extensions. Tooling
validates/indexes Catalog; Catalog gates may use that infrastructure without
making shipped skills depend on it. Executable infrastructure has a real owner;
it is not hidden by support exclusions.

Tests belong to the behavior they exercise. Tooling uses explicit test paths so
future recipe tests in scripts/tests can belong solely to Catalog. The native
audit proves coverage, non-overlap and declared graph/table parity, not every
language import. Native/fixture tests cover declared interfaces; consumer-template
builds and independent agent behavior evaluations remain unmeasured.

Repository PR units and complete reviewer-visible policy live in
[the maintained guide](../repository-gates.md#delivery). There is no separate
constitution or development guide. Support paths remain subject to route audit,
README generation parity where applicable and protected/content review.

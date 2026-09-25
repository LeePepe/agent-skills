---
layer: _root
support:
  - patterns: [AGENTS.md, CLAUDE.md, README.md, .gitignore, docs/**, specs/**, .github/**, .githooks/**, policy/**]
    reason: repository guidance, historical specs and integration entry points checked by contract audit and workflow lint
red_lines:
  - Each tracked path has one owner or one explicit support classification.
  - Tooling reads Catalog; skills remain distributable without importing repository tooling.
---

# Repository architecture

| Layer | Responsibility | tech-context | depends_on |
|---|---|---|---|
| Catalog | Skill packages, bundled scripts/templates, generated registry and marketplace | `skills/tech-context.md` | (none) |
| Tooling | Validation, registry generation, installation helper and repository tests | `scripts/tech-context.md` | Catalog |

The shipped product is the skill catalog, not a deployed application. Tooling validates and indexes
the catalog. CI/hooks invoke the same full verification entry; no executable script is excluded
from ownership. Root support paths remain subject to contract audit and important-path review.

Catalog Markdown and bundled code have different validation depth: local links/frontmatter,
registry consistency, Python/shell syntax and existing deterministic script tests run here.
Consumer-template builds and model behavioral evaluations are not implied by those checks.

There is no separate constitution. Repository-wide privacy, worktree and review constraints are maintained
in [repository policy](../repository-gates.md#review-rules); layer-specific constraints live in the leaves.

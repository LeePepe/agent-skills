# Index-only init output

For init, first locate the target's maintained architecture, leaf contexts, verification/delivery
instructions and dependency manifests/callers. Use those paths, not a fixed new document layout.
The following is a concrete output shape for a repository with the same authorities as this catalog:

```markdown
# Repository entrypoint

## Read first

- Before repository work: [architecture and constraints](docs/architecture/tech-context.md).
- For the affected layer: [Catalog](skills/tech-context.md) or [Tooling](scripts/tech-context.md).

## Protocol

- For dependency revision and commands: [quality caller](.github/workflows/ci.yml).
- Before implementation or push: [versioned protocol](https://github.com/LeePepe/shared-ci/blob/761fe6b0b3ca5e2c57d244182d495ab8041851fa/ai/agent-protocol.md).

## Verify

- Before validation: [verification authority](scripts/tech-context.md).

## Required checks

- Before merge readiness: [gates and current decisions](docs/repository-gates.md).

## Red lines

- Before review: [protected repository policy](docs/repository-gates.md).

## Delivery

- Before publication: [delivery and holds](docs/repository-gates.md).
```

Resolve the selected release from the real caller, then use that revision in protocol/document links.
Keep dependency inventories in their existing manifests/configuration; never ask an AGENTS section to
serve as a lockfile. Preserve unique local rules in their existing layer/gate authorities before removing
the old inline text. All local targets must exist, and each condition must identify when to read them.

Validate an init candidate by following every local route, comparing all provider pins and protocol
links, running native validators and the normal unchanged provider audit. The six headings are valid
directory categories under v0.1.0; they require no embedded rules or commands. Inspect actual lockfile
observations before claiming a dependency declaration is missing. Legacy callers retain honest full-SHA
pointer compatibility. Select the newer `.github/repo-contract.json` metadata (schema, guide, shared_ci,
dependencies) only after choosing a released pin that actually supports that format; use its schema.

When review tools cannot follow links, pass a single tracked/protected authority containing the actual
review-critical rules through both callers' existing `rules-file` input. Preserve trusted-base loading;
do not assume AGENTS links alone supply reviewer context or copy another manual into AGENTS.

For a dry-run decision check, give a reviewer the candidate and an ordinary in-scope test edit/delete:
expect rationale + automatic checks + applicable AI Plan-Review, with no test-only Owner hold. A separate
policy/permission change or explicit human pause must still wait. Use no live dispatch for this check.

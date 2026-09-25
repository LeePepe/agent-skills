# Repository entrypoint

## Read first

- Before repository work: [architecture, ownership and local constraints](docs/architecture/tech-context.md).
- Before editing skills: [Catalog context](skills/tech-context.md), then the affected SKILL.md and its applicable references.
- Before changing tooling: [Tooling context](scripts/tech-context.md).
- For workflow changes or handoffs: [W0–W7 index](skills/workflow/README.md).

## Protocol

- For shared-ci revision and commands: [quality caller](.github/workflows/ci.yml); for its version-specific contract: [published provider docs](https://github.com/LeePepe/shared-ci/tree/761fe6b0b3ca5e2c57d244182d495ab8041851fa/ai).
- Before implementation or push: [current Owner decisions](docs/repository-gates.md#current-owner-decisions) and [pinned repository agent protocol](https://github.com/LeePepe/shared-ci/blob/761fe6b0b3ca5e2c57d244182d495ab8041851fa/ai/agent-protocol.md).

## Verify

- Before validation or recovery: [verification authority](scripts/tech-context.md) and [recovery guidance](docs/repository-gates.md#validation-and-recovery).

## Required checks

- Before assessing merge readiness: [effective versus proposed gates](docs/repository-gates.md#effective-versus-proposed).

## Red lines

- Before reviewing changes: [review-critical rules](docs/repository-gates.md#review-rules).

## Delivery

- Before handoff or publication: [delivery contract](docs/repository-gates.md#delivery) and [bootstrap hold](docs/repository-gates.md#bootstrap-hold).

---
name: fs-codebase-design
description: Design or refine a module interface inside an implementation issue. Use when Fullstack Engineer must choose a seam, reduce an interface, improve testability, or change a module boundary without expanding the issue's authorized scope.
---

# FS Codebase Design

Adapted from Matt Pocock's `codebase-design` skill for full-stack engineering work.

Design a deep module: substantial behavior behind a small interface, placed at a testable seam.

## Vocabulary

- **Module**: anything with one interface and an implementation.
- **Interface**: everything callers must know, including invariants, errors, ordering, configuration, and performance.
- **Seam**: the location where behavior can vary without editing callers.
- **Adapter**: an implementation that satisfies an interface at a seam.
- **Depth**: capability delivered per unit of interface callers must learn.
- **Leverage**: capability reused across callers and tests.
- **Locality**: changes, bugs, knowledge, and verification concentrated in one place.

## Workflow

1. Read the issue's scope and the repository's architecture sources before proposing a seam.
2. State the module, its callers, the current interface, and the behavior that must remain invariant.
3. Apply the deletion test: if removing the module merely removes complexity, it is shallow; if complexity spreads across callers, it is earning its place.
4. Choose the smallest interface that hides the required behavior. Introduce an adapter only when behavior actually varies.
5. Test through the same interface callers use. Prefer accepted dependencies and returned results over hidden construction and side effects.
6. Keep the design inside the issue's authorized files and layer. Report broader architecture work to Team Lead as a re-scope need.

Finish when the chosen interface, invariants, error modes, and verification seam are explicit and the implementation remains within scope.

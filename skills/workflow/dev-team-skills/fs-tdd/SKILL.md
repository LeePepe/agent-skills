---
name: fs-tdd
description: Implement behavior in repository-approved red-green vertical slices. Use when an issue requires test-first work, integration tests, or a regression test and Fullstack Engineer owns both the implementation and its tests.
---

# FS Test-Driven Development

Adapted from Matt Pocock's `tdd` skill for autonomous Multica tasks.

1. Derive the public seam and expected behavior from the issue, spec, repository context, and existing tests. Treat those sources as the agreement; escalate only when they conflict or leave a material product choice open.
2. Write one behavior-focused test whose expected value comes from the spec or another independent source of truth.
3. Obtain a red signal through the repository's authorized verification mechanism.
4. Implement only enough production code to make that slice green.
5. Repeat vertically: one test, one behavior, one minimal implementation.
6. Refactor only after green, preserving behavior through the public interface.
7. Run the repository-defined completion gates and report exact evidence.

Repository instructions decide how tests execute. If direct test commands are forbidden and hooks or CI own execution, use those gates for red and green evidence. Never bypass, weaken, or duplicate the repository's quality gates.

Avoid implementation-coupled mocks, private-method tests, tautological expectations, and speculative behavior outside the issue.

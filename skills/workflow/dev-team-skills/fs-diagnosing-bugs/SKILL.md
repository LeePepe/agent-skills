---
name: fs-diagnosing-bugs
description: Reproduce, diagnose, and fix code or local-service defects with a tight feedback loop. Use when Fullstack Engineer receives a bug, failing test, crash, broken integration, or performance regression and owns the resulting implementation.
---

# FS Diagnosing Bugs

Adapted from Matt Pocock's `diagnosing-bugs` skill and the former Multica Debugger role.

## Tight loop

1. Read the issue, repository instructions, domain context, and relevant ADRs.
2. Build one fast, deterministic, agent-runnable check that fails on the reported symptom. Redact credentials and sensitive payloads from every artifact.
3. Reproduce the exact symptom, then minimize the scenario until every remaining input or dependency is load-bearing.
4. Record three to five ranked, falsifiable hypotheses. Probe one prediction at a time with targeted instrumentation.
5. Fix the root cause at the smallest authorized seam. Add a regression test when the repository provides a valid test surface.
6. Re-run the original check and repository-defined gates. Remove temporary logs, harnesses, sockets, and debug code.

Use safe user-domain diagnostics for local services. When diagnosis requires administrator approval, external credentials, unavailable hardware, or files outside the issue scope, stop mutation and hand Team Lead the evidence, required authority, and next action.

Finish only when the original symptom is green with fresh evidence, or when a structured blocked/re-scope handoff identifies the unresolved dependency.

# Archify Contract

Use `tt-a1i/archify` workflow typed JSON with locale `zh-CN`.

For each source JSON:

```bash
node /path/to/archify/bin/archify.mjs validate workflow INPUT.json --quality showcase --json
node /path/to/archify/bin/archify.mjs deliver workflow INPUT.json OUTPUT.html --quality showcase --json
node /path/to/archify/bin/archify.mjs visual-check OUTPUT.html --json
```

Require all showcase checks, zero errors, and zero warnings. Visually inspect the delivered artifact. JSON is the source of truth; do not hand-edit generated HTML or alter JSON after its final passing validation.

The generic diagram is reusable. Per-team/repository and per-P0/P1 diagrams are audit outputs generated from observed evidence, not bundled guesses.

When auditing Multica supervision, depict Autopilot as a separate control-plane actor: operational dispatch/rerun/report links, repair ownership returning to Dev Team, and exact-SHA PR intake independent of authorship. Distinguish physical execution daemon from provider-specific runtimes in the relationship diagram; show an independently hosted observer only when deployment evidence supports it. Follow [autopilot-contract.md](autopilot-contract.md).

The bundled generic diagram covers delivery/recovery/audit and does not yet depict Autopilot. For a supervision audit, supplement it with a freshly validated relationship diagram based on the written contract and current evidence; do not present the bundled illustration as complete supervision coverage.

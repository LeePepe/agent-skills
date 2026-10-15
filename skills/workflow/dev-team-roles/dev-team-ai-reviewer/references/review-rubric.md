# AI Reviewer supplement

Use with the companion `review-agent` skill. [SKILL.md](../SKILL.md) governs scope,
round budgets, coverage and blocking exceptions, and wins any conflict.

## Checking against the spec/ACs

Compare the pinned diff and accepted spec/ACs directly; implementation reports are claims to check.
Classify each conformance gap:

- **Missing**: required behavior or evidence was omitted or claimed without implementation.
- **Extra**: behavior was built that the accepted scope did not request.
- **Misunderstood**: the implementation addresses the requirement with the wrong behavior.

For an AC that the pinned diff and spec cannot establish, write `⚠️ cannot verify`, identify
the AC and missing evidence, and declare the coverage gap. Do not broaden the search or invent
requirements. A coverage gap is not proof of a defect; insufficient coverage cannot earn `PASS`.
Calibrate by actual impact: "coverage could be broader" or polish alone is minor and non-blocking;
missing proof explicitly required by an AC or mandatory rule is assessed against that source.

## Re-review (rounds >=2) output

Use these entries in order; a re-review checks prior findings and the repair diff:

1. **Prior findings**: for each prior finding, report `ADDRESSED` or `NOT ADDRESSED` with
   file:line evidence. A repair attempt counts only when the specific defect is gone.
2. **New breakage in the repair diff**: list concrete regressions with severity, source and
   file:line evidence, or `None`.
3. **Missed blockers**: a late P0/P1 or mandatory-rule violation outside the repair diff still
   blocks under SKILL.md. Label it `missed-in-round-N`, where N is the round that missed it,
   explain the miss, and cite pinned evidence and the trigger.
4. **Out-of-scope observations**: other observations outside the repair diff are non-blocking
   follow-ups; list them separately or write `None`. They do not extend the review loop.
5. **Round verdict**: give the round number, exact revision/SHA and `PASS` or `NEEDS_WORK`,
   naming any remaining blockers or coverage gaps.

Follow SKILL.md's round budget and escalation rules; this output grants no additional round.

## Verdict mapping

- **P0/P1** → `NEEDS_WORK` (blocking).
- **P2/P3** → non-blocking follow-ups; they do not prevent `PASS`.

Mandatory-rule violations still block where SKILL.md requires it. `PASS` also requires a pinned
revision and sufficient coverage; follow SKILL.md's escalation rules when the budget is exhausted.

## Sources

Adapted; wording paraphrased.

- [Superpowers task-reviewer-prompt.md](https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/task-reviewer-prompt.md) — MIT.
- [Superpowers re-review-prompt.md](https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/re-review-prompt.md) — MIT.
- Companion: [Codex review-agent/SKILL.md](https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/review-agent/SKILL.md) — Apache-2.0; supplies finding criteria, priorities and finding format.

# AI Reviewer supplement

Use with the companion `review-agent` skill. The `execution-contract` skill
governs scope and rounds; [SKILL.md](../SKILL.md) supplies role-specific pinning and output.

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

Use these entries in order; contract V3 limits re-review to prior findings and the repair diff;
do not rescan unchanged code:

1. **Prior findings**: for each prior finding, report `ADDRESSED` or `NOT ADDRESSED` with
   file:line evidence. A repair attempt counts only when the specific defect is gone.
2. **Repair-diff regressions**: list problems introduced by the repair under contract V2, with the
   severity, cited source, trigger and file:line evidence regardless of which file is affected.
   These block; otherwise write `None`.
3. **Other findings / backlog**: apply contract V2; cite any remaining blocking findings with pinned
   evidence and trigger. Label previously missed blockers `missed-in-round-N`. Pre-existing problems
   that meet none of V2's blocking conditions go to backlog and do not block.
4. **Round verdict**: give the round number, exact revision/SHA and `PASS` or `NEEDS_WORK`,
   naming any remaining blockers or coverage gaps.
   End the comment with the same machine-readable review line immediately before the requester mention,
   as defined in [SKILL.md Handoff](../SKILL.md#handoff-one-final-comment-in-the-multica-thread).

Follow SKILL.md's round budget and escalation rules; this output grants no additional round.

## Verdict mapping

Apply contract V1–V3 before assigning a verdict; use V2's introduced/pre-existing classification
and blocking conditions regardless of file path. `PASS` requires a pinned revision and sufficient evidence for the Target's
checks (or prior findings and repair-diff regression checks on re-review); route exhausted rounds through TL to the definer.

## Sources

Adapted; wording paraphrased.

- [Superpowers task-reviewer-prompt.md](https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/task-reviewer-prompt.md) — MIT.
- [Superpowers re-review-prompt.md](https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/re-review-prompt.md) — MIT.
- Companion: [Codex review-agent/SKILL.md](https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/review-agent/SKILL.md) — Apache-2.0; supplies finding criteria, priorities and finding format.

# Owner Decision Packet

Escalate one irreducible decision per packet. Deduplicate by:

`scope + decision_type + subject_id + unresolved_authority_conflict`

Use this shape:

```markdown
## Decision <stable-id>: <plain-language question>

- Scope: <project / issue / PR / workflow>
- Type: feature | scope | priority | acceptance | workflow | authority | risk | cost | credential | recovery
- Urgency: now | before <event> | can wait
- Safe state now: <what remains paused or continues>
- Why existing authority cannot decide: <conflict or missing decision>
- Evidence: <stable issue/run/PR/SHA/check/finding references>

### Options

1. <option and consequence>
2. <option and consequence>

### Recommendation

<one option, the evidence-based reason, and its tradeoff>

### Reply needed

<the smallest answer that resolves the decision>
```

Include no more than three mutually exclusive options. Put the recommended option first. State the reversible safe default when the Owner does not answer by the relevant event.

Approval authorizes only the stated decision. A workflow audit finding approved for remediation still requires a separately scoped executor or Dev Team task; the supervisor does not implement it.

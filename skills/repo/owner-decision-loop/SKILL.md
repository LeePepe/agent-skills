---
name: owner-decision-loop
description: Resolve delivery decisions through reusable owner calibration. Use when Team Lead cannot determine Planner or Fullstack content from repository authority because product intent, acceptance, scope, architecture, policy, terminology, or conflicting evidence requires the owner's choice; do not use for routine implementation decisions already delegated to a role.
---

# Owner Decision Loop

Turn one unresolved delivery conflict into an explicit owner choice, route that choice to the role that owns the content, and make the result reusable for later decisions.

## 1. Prove that a decision is needed

Build a decision packet from the triggering issue, exact artifacts or SHA, conflicting findings, and attempted safe resolutions. Bind the search to the exact repository/issue revision and record which source classes were searched, including an explicit `none found` result. Search existing authority in this order:

1. constitution and explicit owner decisions;
2. applicable ADRs and domain context;
3. active spec and accepted product evidence;
4. plan, contracts, and layer tech-context;
5. issue-scoped decisions and current handoffs.

Reuse an existing decision only when its scope, assumptions, and effective revision still match and no higher-precedence source supersedes it. Cite the source and route the work without asking again. A governing constraint may eliminate options without selecting the remaining product outcome; open a narrower owner decision when more than one compliant outcome remains.

Return routine implementation choices inside accepted scope to Fullstack Engineer. Return planning synthesis already determined by repository authority to Planner Lead. Ask the owner only when a real choice remains.

## 2. Ask a decision-sized question

Send one compact packet:

```markdown
## Decision needed
<one sentence question>

### Conflict and evidence
<what cannot simultaneously be true, with source links>

### Options
- A — <choice>; impact on product, Planner, FS, risk, and reversibility
- B — <choice>; impact on product, Planner, FS, risk, and reversibility
- C — <choice>; only when genuinely distinct

### Recommendation
<one option and why, with any external assumption labeled; or "No evidence-based recommendation" when owner preference is the missing input>

Reply with A/B/C or a replacement decision.
```

Keep orthogonal choices separate. Do not hide a second decision inside an option. Make no content or shipping mutation while awaiting the answer.

## 3. Record the decision

After the owner answers, publish an interim issue decision record containing:

- question and chosen answer;
- scope and affected artifacts/tasks;
- assumptions and constraints;
- effective revision/date;
- sources considered;
- superseded decision, if any;
- roles responsible for persistence and execution.

TL owns the interim record and routing, not the canonical content edit. Place durable truth through the role that owns its canonical artifact:

- global invariant or governance → constitution;
- canonical terminology → `CONTEXT.md`;
- hard-to-reverse architectural trade-off → ADR;
- product outcome, behavior, acceptance, or non-goal → `spec.md`;
- feature-local design or contract → `plan.md`, `research.md`, or `contracts/`;
- layer dependency, red line, or verification rule → layer tech-context;
- one-off execution choice → issue decision record only.

Use references instead of copying one decision into several sources.

## 4. Route and learn

- Send planning, domain, ADR, constitution, and tech-context persistence to Planner Lead with the exact owner decision.
- Send implementation-local execution to Fullstack Engineer only after the governing planning artifact or issue decision is explicit.
- Re-enter the normal independent review gate after content or code changes.
- Keep issue lifecycle and cross-role scheduling with Team Lead.

Future runs may decide automatically from the recorded source when the scope and assumptions match. Any mismatch, contradiction, or superseding evidence opens a new owner decision instead of stretching the old one.

Use [eval-cases.md](references/eval-cases.md) when changing this skill or checking whether a runtime preserves the automatic-decision, owner-question, and role-boundary branches.

Finish with a cited automatic decision, one pending owner question, or a recorded decision routed to the exact owning role.

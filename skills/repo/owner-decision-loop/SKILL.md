---
name: owner-decision-loop
description: Resolve owner choices or unresolved repair investigations when existing repository authority cannot decide. Use for product, scope, architecture, policy or evidence conflicts, or failed diagnosis by Team Lead or the original subagent coordinator. Routine implementation remains with its owner.
---

# Owner Decision Loop

Turn one unresolved conflict or repair investigation into an explicit owner choice. Route decisions to the role that owns the content; keep Team Lead for Dev Team and the existing main conversation for subagents, without adding a supervisor.

Read the [workflow contract](../../workflow/README.md) for fixed execution versions and the two-round repair escalation trigger. An escalation does not authorize a new version, replacement executor, or weaker acceptance.

## 1. Prove that a decision is needed

Build a decision packet from the triggering issue, exact artifacts or SHA, conflicting findings, and attempted safe resolutions. Bind the search to the exact repository/issue revision and record which source classes were searched, including an explicit `none found` result. Search existing authority in this order:

1. constitution and explicit owner decisions;
2. applicable ADRs and domain context;
3. active spec and accepted product evidence;
4. plan, contracts, and layer tech-context;
5. issue-scoped decisions and current handoffs.

Reuse an existing decision only when its scope, assumptions, and effective revision still match and no higher-precedence source supersedes it. Cite the source and route the work without asking again. A governing constraint may eliminate options without selecting the remaining product outcome; open a narrower owner decision when more than one compliant outcome remains.

Return routine implementation choices to the original FS/subagent. Return planning synthesis to the existing planning owner. Ask the owner when a real choice remains, or diagnosis by TL/the original main conversation cannot resolve the repair blocker—even when its cause is unknown.

For repeated repairs, attach each fix, verification and review result to the same root problem across task/run/SHA changes. After two rounds without progress, TL/the existing main conversation diagnoses; the original implementer retains repairs. Hard safety/permission blockers are reported immediately. Preserve evidence and independent authorized work rather than retrying indefinitely or deferring the current defect as a new requirement.

For an unreproduced or fact-incomplete report with no safe useful next step, deliver the investigation evidence and unknowns to the Owner. The original repair remains incomplete. Once in this wait, new evidence or restored conditions cannot restart execution: wait for the Owner to choose continuation through the original task and responsibility. Do not record “not reproduced” as “no defect” or “fixed”.

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

For an unresolved technical blocker, send the failed requirement and impact, fixed task/plan revision, attempts and results, established cause or `unknown`, and recommended next step with any help/decision needed. Do not invent A/B/C choices or pretend the owner knows the root cause. The hold applies to affected work, not unrelated tasks.

## 3. Record the decision

After the owner answers, publish an interim issue decision record containing:

- question and chosen answer;
- scope and affected artifacts/tasks;
- assumptions and constraints;
- effective revision/date;
- sources considered;
- superseded decision, if any;
- roles responsible for persistence and execution.

TL (Dev Team) or the existing main conversation (subagent path) owns interim routing, not a replacement implementation lane. Place durable truth through the existing owner of its canonical artifact:

- global invariant or governance → constitution;
- canonical terminology → `CONTEXT.md`;
- hard-to-reverse architectural trade-off → ADR;
- product outcome, behavior, acceptance, or non-goal → `spec.md`;
- feature-local design or contract → `plan.md`, `research.md`, or `contracts/`;
- layer dependency, red line, or verification rule → layer tech-context;
- one-off execution choice → issue decision record only.

Use references instead of copying one decision into several sources.

Distinguish agreement with an idea from approval to execute a whole version. New goals/material changes return to the same requirements intake, keeping the current execution version fixed. Record explicit execution approval before handing the new version to implementers. In-scope implementation/test supplementation and current defects remain in the current plan. A discussion record alone is not implementation authority.

## 4. Route and learn

- Send canonical planning changes to the existing planning owner with the exact decision; subagents need no extra Dev Team task graph.
- Send implementation-local execution to the original FS/subagent only after the governing planning artifact or issue decision is explicit.
- Re-enter the normal independent review gate after content or code changes.
- Keep team dependency scheduling with TL, subagent scheduling with the original main conversation, and non-Draft PR lifecycle with PRM. Fundamental external-PR conflicts follow the [source-specific notification boundary](../../workflow/README.md#prm-唯一交付责任), not an automatic Owner question.

Future runs may reuse a recorded decision when scope, assumptions and effective version match. Reuse never supplies a missing answer to an active Owner wait. A mismatch or superseding evidence reopens only the affected decision, preserving the prior record and unaffected conclusions.

Use [eval-cases.md](references/eval-cases.md) when changing this skill or checking whether a runtime preserves the automatic-decision, owner-question, and role-boundary branches.

Finish with a cited automatic decision, one pending owner question/blocker report, or a recorded decision routed to the exact owning role.

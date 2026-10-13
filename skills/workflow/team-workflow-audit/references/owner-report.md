# Owner-First Report

Write the primary report for the Owner before the technical audit appendix. Use the report locale and explain the result without requiring knowledge of audit enums.

## Required order

1. Two to four answer-first conclusions.
2. What needs attention now.
3. What decision or owner is needed.
4. Plain-language metrics.
5. Technical audit appendix.

The first page must stand alone. A reader must not need the appendix to understand whether delivery is trustworthy, whether agents followed their rules, or whether the workflow repeatedly stalled.

## Plain-language mappings

Translate the four axes before showing their technical names:

| Audit axis | Owner question | Positive | Negative | Unknown |
|---|---|---|---|---|
| Workflow Conformance | Agent 有没有按当时规则做该做的事、避免做越权的事？ | confirmed rule-following | confirmed rule violation | cannot determine |
| Workflow Fitness | 即使 Agent 按规则做，这套流程能否顺畅完成？ | workflow can complete | workflow is unfinishable or repeatedly stalls | cannot determine |
| Outcome Integrity | 最终交付是否确实对应审查、测试和需求？ | confirmed trustworthy delivery | confirmed delivery-integrity failure | cannot determine |
| Task Effectiveness | 实际发布和使用后，任务是否真的解决？ | confirmed effective | confirmed ineffective or regressed | pending delivery/release/observation or cannot determine |

Keep the exact enum in parentheses only after the plain-language label when useful.

## Answer-first summary

Front-load the answer, numbers, and decision meaning. Keep the summary to two to four conclusions. Put method, enum definitions, evidence mechanics, and supporting detail later.

For Workflow Conformance, Workflow Fitness, and Outcome Integrity, render all three buckets together as direct labels and counts:

> 最终交付：可信 18｜不可信 0｜尚未判定 22

The three values must reconcile to the denominator. Treat unknown as its own bucket in validation and data, without adding a sentence that explains it is not success.

Render Task Effectiveness with four Owner-facing groups:

> 任务实际效果：确认解决 X｜未解决或复发 Y｜等待交付/发布/使用 Z｜尚无足够证据 W

Keep `ineffective` and `regressed` separate in structured data and the technical appendix.

Expand the unknown bucket only when its composition changes the Owner's decision:

> 尚未判定 22：未完成 16｜缺关闭证据 6

## No meta-explanation

Summary sentences contain a new fact, impact, action, or decision. Delete sentences that only tell the reader how not to interpret information already visible in labels and numbers.

Avoid phrases such as “这不表示……”, “不要误解为……”, “需要注意的是……”, “换句话说……”, or “准确含义是……”. Replace them with the missing fact or delete them.

State boundaries directly:

> 当前授权：仅审计；未授权修复。

Caveats stay next to the affected claim only when they change its interpretation or the Owner's action.

## Owner summary schema

Produce this structure in the snapshot or a linked owner-summary artifact:

```json
{
  "owner_summary": {
    "total_cases": 0,
    "delivery_trust": {
      "confirmed_trustworthy": 0,
      "confirmed_compromised": 0,
      "unknown": 0
    },
    "rule_following": {
      "confirmed_following": 0,
      "confirmed_violations": 0,
      "unknown": 0
    },
    "workflow_usability": {
      "confirmed_fit": 0,
      "confirmed_unfit": 0,
      "unknown": 0
    },
    "task_effectiveness": {
      "confirmed_effective": 0,
      "confirmed_ineffective": 0,
      "confirmed_regressed": 0,
      "pending": 0,
      "unknown": 0
    },
    "top_concerns": [],
    "owner_actions": []
  }
}
```

Counts must reconcile to `total_cases` for each axis. Keep project-level breakdowns when more than one project is audited.

## Findings

Present every P0/P1 finding first in this owner-facing shape:

1. **发生了什么**
2. **为什么重要**
3. **是否已影响最终结果**
4. **目前知道什么 / 不知道什么**
5. **谁应处理**
6. **当前状态**

Then link to the technical fingerprint, event IDs, SHA evidence, and Archify chain. Do not lead with a fingerprint or enum.

## Metrics

Give every metric:

- a plain-language name;
- one sentence defining what is counted;
- numerator and denominator where a rate is implied;
- the highest-impact subjects;
- evidence limitations.

Label agent repetition as activity count. Keep rule violations in the separate rule-following result. State whether same-artifact versus changed-artifact identity is fully observed or only a lower bound.

## Technical appendix

Preserve the exact audit schema in the appendix:

- Workflow Conformance / Fitness / Outcome Integrity enums;
- Task Effectiveness lineage, verdict, release/build, and observation evidence;
- finding priority and lifecycle;
- stable fingerprints;
- event IDs and evidence references;
- per-role repeat metrics;
- cohort, cursor, instruction hashes, and limitations.

Do not put raw JSON objects in the Owner summary table. Use labels and counts.

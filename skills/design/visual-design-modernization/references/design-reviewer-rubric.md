# Design Review Rubric (7 dimensions)

Canonical scoring rubric shared by the `design-reviewer` agent and this skill. Score each
dimension 1–5 (5 = best); total out of 35. Any dimension < 4 must get a concrete problem + a
concrete fix with suggested values.

| # | Dimension | What "good" looks like | Classic 🚩 fault |
|---|-----------|------------------------|------------------|
| 1 | **Spacing & whitespace** | consistent 4/8/12/16/24/32 scale; generous even padding; right density | full-bleed no max-width → stretched sparse; random 10/15/18 |
| 2 | **Typography hierarchy** | ≥3 levels (title/body/meta); weight contrast; rounded/tabular numbers; body lineSpacing | one size + one grey everywhere |
| 3 | **Color & contrast** | restrained system semantics; status colors sparing; adequate contrast; ≤1 accent/card | garish pure green/orange, or all-grey monotone |
| 4 | **Hierarchy & elevation** | cards float (shadow OR luminance tiers); eye guided to key info | flat outline-only, fused with bg |
| 5 | **Grouping & alignment** | related items grouped; consistent grid; parallel metrics each own card | metrics crammed in one big card |
| 6 | **Data visualization** | sparkline for trend, ring/bar for ratio; palette consistent; restrained | dashboard with only ↑↓ arrows |
| 7 | **Platform fit** | HIG feel: system fonts/colors/radii/materials; auto dark+Dynamic Type | web-style harsh shadows, non-system colors, oversized radii |

## Scoring guidance
- **30–35**: ship-ready, only P1 polish left.
- **24–29**: solid direction, a few P0 hard faults to fix.
- **< 24**: fundamental issues (usually spacing/hierarchy/elevation) — fix before iterating on detail.

## Output contract
```
# 设计评审结果
**总分: XX / 35** — one-line verdict
## 维度评分  (table, all 7 rows)
## 必修项 (P0)  — problem → concrete fix + values
## 建议项 (P1)
## 做得好的地方 (keep)
```

## Reviewer discipline
- Specific > vague; always give numbers (pt, font, color, shadow params).
- P0 = ugly-at-a-glance; P1 = refinement. P0 first.
- Honest: praise real wins, don't soften real faults — the user relies on objectivity to
  substitute for design experience.
- UI only; no feature/architecture edits.
- Match the caller's language.

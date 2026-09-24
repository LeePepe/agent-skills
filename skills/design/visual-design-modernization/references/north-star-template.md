# North-Star Template

> Copy this into a project as `design/north-star.md` and fill in the brackets.
> This file is the **visual target** the `design-reviewer` scores against. Keep every rule
> concrete and checkable (px values, font steps, color roles) — not adjectives.
> Reference sources are public apps you can just look at; **no Figma needed**.

## 0. One-line principle

> [e.g. 留白舍得给,层级拉得开,数字配上图,配色管得住 — whitespace, hierarchy, charts, restrained color]

Faults this redesign fixes (fill from the diagnose step):
| Fault | Fix |
|---|---|
| [full-bleed sparse] | [max content width ~1200pt centered] |
| [KPIs in one big card] | [independent cards, responsive grid] |
| [no charts] | [sparkline + ring next to numbers] |
| [flat + one font] | [elevation + ≥3 type levels + status pills] |

North-star references: [Linear / Vercel dashboard / Apple system apps — pick the ones whose feel you want].
Design philosophy: [e.g. Apple-native restraint as the base + modern-dashboard density].

## 1. Layout & grid
- **Max content width:** [1200]pt, centered (`.frame(maxWidth: X).frame(maxWidth: .infinity)`).
- Page horizontal padding: [24 mac / 20 iOS]. Vertical: [28].
- Section spacing: [32]. Section header → first item: [12].
- KPI grid: `LazyVGrid(.adaptive(minimum: [220], maximum: [320]), spacing: [16])`.
- Card gap within a group: [16].

## 2. Spacing scale (only these — no random numbers)
`2 4 8 12 16 20 24 28 32 40`

## 3. Typography — ≥3 levels
| Role | Font | Use |
|---|---|---|
| Page title | `.largeTitle.bold()` | top header |
| Section label | `.caption.weight(.semibold)` + `.tracking(0.8)` + `.textCase(.uppercase)` + secondary | section headers |
| KPI number | `.system(size:[34], weight:.bold, design:.rounded)` | the focal number |
| Card title | `.headline` | prose card header |
| Body | `.callout`/`.body` + `.lineSpacing(3)` | paragraphs |
| Meta | `.caption` secondary | timestamps / refs |
| Pill text | `.caption2.weight(.semibold)` | status badges |

Rules: numbers use `.rounded`; long body gets `lineSpacing`; ≥3 weights on screen.

## 4. Color — restrained, semantic
- System semantic colors only; **no hex/RGB hardcode**.
- Body text never `.tertiary`; `.secondary` for secondary only.
- ≤1 accent anchor per card.
- Status: success→green, warning→orange, danger→red, neutral→secondary.
- **Status pill:** `color.opacity(0.12–0.20)` fill + full-saturation text, `Capsule`, padding `h8/v3`.

## 5. Card & elevation — pick ONE scheme, be consistent
- Background one step above page.
- Radius: [KPI 18 / prose 20], `.continuous`.
- **Either** soft shadow `shadow(color:.black.opacity([0.06]), radius:[8], y:2)`
  **or** flat luminance tiers (L0 bg < L1 card < L2 inner) + 1px hairline border.
- Page background always one step below card so cards float.

## 6. KPI card structure
Label (caption uppercase secondary) → big number (rounded bold) + unit + trend arrow → status pill → sparkline / ring. Ratio metrics use a ring gauge.

## 7. Data-viz
- Sparkline: area(gradient) + line, ~40pt, axes hidden, optional baseline + endpoint dot.
- Ring: `Gauge` or trimmed `Circle`; keep a start dot + colored center text visible even at 0%.
- Palette same hue family as brand (see color-system.md).

## 8. Prose card
Header row: badge + title + timestamp. Body: `lineSpacing`, grouped whitespace, row dividers, left status dot + status pill instead of grey text.

## 9. Acceptance checklist (reviewer scores these)
- [ ] max content width, not stretched
- [ ] KPIs independent cards, columnar
- [ ] sparkline/ring next to each number
- [ ] cards elevated (one consistent scheme)
- [ ] ≥3 type levels
- [ ] status as colored pills
- [ ] restrained system colors, no hex
- [ ] long body has lineSpacing, groups have whitespace

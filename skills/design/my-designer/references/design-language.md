# Design language — one system per platform

The lead owns the north-star and integration. Web uses **Basalt + Recharts**;
native SwiftUI retains the native kit. Shared quality goals do not require
forcing identical implementations or web dependencies across platforms.

## React web: real Basalt

Use `@nocoo/basalt` public components and its token/provider system. Read
[basalt-web.md](basalt-web.md) before integration. The library, not an app-local
`makePrimaryPalette` or copied legacy `theme.ts`, is the web visual authority.

- **Chrome:** compose `AppShell`, `Sidebar`, `AppMain`, `AppHeader`,
  `ContentIsland`, `PageHeader`, and `LayerCard`. The app supplies brand,
  navigation and page content. Do not reproduce the chrome with lookalike divs.
- **Surfaces:** preserve Basalt's matte outer canvas, content island and nested
  card hierarchy. Use its surface, border, radius and spacing vocabulary;
  arbitrary component shadows and hardcoded palettes undermine it.
- **Controls:** use official buttons, inputs, tabs, tables, dialogs and badges
  where public components fit. App-owned composition handles product-specific
  behavior; a missing primitive must be disclosed, not sold as a library API.
- **Theme:** one root owner for theme persistence and document mutations. Use
  Basalt's supported accent configuration if needed. Brand accent and chart
  palettes are separate: changing accent must not remap financial semantics.
- **Charts:** Recharts 3, directly or through Basalt chart wrappers. Use Basalt
  chart tokens/utilities for series, axes, legends and tooltips. Check installed
  palette/API behavior rather than assuming a fixed palette length.

The legacy web templates remain explicit opt-in resources, not an alternative
automatic routing choice. If chosen by the user, keep their seed/theme system
internally consistent and identify the result as legacy, not Basalt.

## Shared product quality

- Establish a readable hierarchy: page title, section label, primary value,
  supporting metadata. Align numbers with tabular figures; format units,
  currencies, signs, dates and precision consistently.
- Use responsive content density. Bound reading/chart areas, let useful tables
  use available width, and avoid wide empty cards. Do not force every screen
  into a universal 1200px column if the actual workflow needs more room.
- Choose charts to answer questions: line/area for history, bars for comparison,
  composition charts for a meaningful whole. Avoid decorative sparklines or
  gauges when no history or denominator exists. Pair charts with readable values
  and accessible summaries or tabular alternatives.
- Keep category/series identities stable across views and themes. Use labels,
  shape or pattern alongside color. Income/expense and gain/loss must follow
  the product's financial conventions, not a universal “green means good” rule.
- Keep primary actions apparent, focus visible and targets usable by touch.
  Validate keyboard navigation, drawer/dialog focus, chart tooltips, long names,
  narrow screens and reduced motion.
- Loading, empty, filtered-empty and errors are distinct states. Errors must not
  look like zero balances or valid demo data. Privacy mode covers charts,
  tooltips, accessible text and details, not only headline numbers.
- Preserve drill-down and return context. An attractive overview without working
  detail screens is not a complete app.

## Native SwiftUI

Retain the supplied `templates/swiftui/` design kit and
[`makePrimaryPalette` color specification](../../visual-design-modernization/references/color-system.md).
Native views use `theme.neutrals.*`, `theme.primary.*`, and `theme.chart(i)`;
hex values live in the color-system source. Start with blue/slate unless the
brief selects another seed/neutral. Semantic colors remain independent of seed.

Use luminance-tier surfaces and consistent borders, native typography with
monospaced digits, and the kit's `Card`, `Metric`, `Sparkline`, `RingGauge`,
`StatusPill`, and `ThemeControl` where appropriate. Preserve native interaction
and accessibility rather than approximating browser layouts.

## Review acceptance

Give `design-reviewer` actual rendered screenshots, the selected platform and
this north-star. Review representative overview, dense list, detail and mobile
screens where present; theme or filter state must match the supplied screenshot.
Request /35 plus P0/P1 findings with concrete fixes. Also inspect implementation
evidence for real Basalt imports: a screenshot alone cannot prove library use.

Fix P0, resolve or disclose P1, rerender changed screens and report the real gate
outcome. With no screenshot/reviewer, disclose the missing evidence; do not
fabricate a score. User direction approval remains separate from this gate.

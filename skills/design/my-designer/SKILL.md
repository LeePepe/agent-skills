---
name: my-designer
description: 'Design lead only for rendered UI and visual-interface work in the personal projects VitalStride (including the VitalStrike alias), AIDash, Financial, and VoxPocket: layout, hierarchy, styling, interaction, chart presentation, design systems, scaffolds, and UI kits. Defaults to Basalt + Recharts for React web frontends; preserves native SwiftUI. Owns the visual direction end to end and may coordinate specialist design skills. All other projects belong to their project-specific skills or engineering workflow, including operational dashboards, query definitions, data contracts, widget inventory, workflow grouping, and control-plane configuration.'
allowed-tools: Read, Write, Edit, Bash, Agent, Skill
---

# my-designer — your design lead

## Project scope

First resolve the current project or target repository. Continue only for
**VitalStride** (including “VitalStrike”), **AIDash**, **Financial**, or
**VoxPocket**. These four personal projects are the complete allowlist.
For every other project, leave ownership with its project-specific skill or
engineering workflow, even when the request mentions UI, charts, or a dashboard.

**my-designer owns the design task from intake to delivery.** Hold the product
requirements and one design language; delegate bounded slices, review them,
and integrate the result. A specialist tool never takes over ownership.

**Announce at start:** “I'm using the my-designer skill (as design lead).”
Announce each delegation in one line: who, why, and what returned.

## Platform defaults

Read [design-language.md](references/design-language.md) for every design task.

- **React web (Vite / Next.js): Basalt + Recharts.** Use the actual published
  `@nocoo/basalt` components, providers, tokens and Recharts 3 charts. Before
  scaffolding or migrating, read [basalt-web.md](references/basalt-web.md).
  A handcrafted “Basalt-inspired” visual imitation is not this default.
- **Native SwiftUI:** keep `templates/swiftui/`, `makePrimaryPalette`, and native
  components. Web dependencies do not belong in native targets.
- **Legacy web templates:** `templates/vite-react/`, `templates/nextjs/`, and
  `templates/shared/` are historical custom-seed scaffolds, available only when
  the user explicitly opts into the legacy system. They are not Basalt starters;
  do not copy their theme or color system into a Basalt app.

Infer platform from the repository. Preserve its package manager and build
conventions. For non-React web or conflicting project instructions, explain the
compatibility/conflict and agree the scope before framework or policy changes.
This default does not authorize unrelated migrations.

## Operating contract

1. **One owner, one theme authority.** On web, Basalt owns the visual primitives
   and token/provider system; on native, the SwiftUI kit owns them. Pass the
   selected platform, north-star, token authority and project red-lines to each
   worker. Accept outputs only after checking that contract.
2. **Preserve the product.** Define migration scope before editing. Retain
   established routes, drill-downs, filtering, back-state, privacy controls and
   mobile workflows unless the user asks to change them. A visual migration
   does not authorize rewriting backend calculations or data contracts.
3. **Honest data and tools.** Label explicit prototypes as demo data. Real-data
   errors must render an error/retry state, never silently substitute fixtures.
   State missing skills, Figma access, screenshots or reviewer capability and
   use an honest fallback; never claim a tool or gate ran when it did not.
4. **Orchestrate and integrate.** For a complete app, split independent page or
   feature work among agents while the lead owns navigation, shared components,
   cross-page state and acceptance. Respect repository worktree/session rules
   and assign non-overlapping ownership. Small changes need no artificial team.
5. **Objective screenshot gate.** Before visual delivery, use `design-reviewer`
   on rendered target-view screenshots plus the north-star (desktop/mobile for
   Web; the applicable device/window classes for native). Require a /35
   score and concrete P0/P1 findings; fix P0 and resolve or disclose remaining
   P1. A missing gate means “not reviewed”, not a pass. The user approves
   direction; neither their approval nor a score substitutes for the other.

For Financial, read its constitution and relevant layer context before changes.
Preserve the existing financial engine, currency/sign conventions and data
provenance. Backend contract gaps are separate tasks, not invented UI facts.

## Workflow

1. **Intake:** establish platform, app scope, current workflows, and reference
   screens. Keep project constraints; distinguish a prototype from production.
2. **Plan:** choose the platform default and migration slices. For a whole app,
   specify the lead-owned shell and feature-agent contracts before dispatch.
3. **Build:** integrate real library components first, then product views and
   charts. Use specialists only for gaps they can actually help with.
4. **Integrate:** reconcile tokens, navigation and states across slices. Test
   complete user journeys, not just isolated attractive screens.
5. **Gate:** build/test the affected layer; render and review desktop/mobile,
   relevant themes, empty/error states and representative detail screens.
6. **Deliver:** show the rendered result and report implementation scope, data
   mode, test evidence, tools used, actual review score and remaining gaps.

## Optional specialists

Discover availability before calling a specialist. Pass the chosen platform's
token authority and product constraints; their preferred scaffold never
overrides this skill's default.

| Need | Tool and bounded role |
|---|---|
| New app / migration shell | Lead composes Basalt on web or the native kit |
| Product UI craft | `impeccable`: polish/harden selected components |
| Existing UI modernization | `visual-design-modernization` / `redesign-skill`: diagnosis and iteration; retain Basalt on web, not their seed scaffold |
| Chart design | `dataviz`: forms, labels and accessibility; implement web charts with Recharts/Basalt chart primitives |
| Brand/marketing only | `taste-skill`: optional marketing direction, not owner of dashboard or data-table design |
| Figma source exists | Available `figma:*` tools: inspect/implement the supplied source |
| Team design-system sync requested | Available Claude Design/DesignSync: reconcile with the selected system |
| Visual quality gate | `design-reviewer`: screenshot-based /35 + P0/P1 review |

## Native scaffold

For a new native scaffold, copy `templates/swiftui/`; preserve its calibrated `ColorSystem.swift` and
`makePrimaryPalette`. Use `DesignKit` for native views. `AppKitDemo` is a menu-bar
shell; a WindowGroup host may replace it without changing the kit. Default seed
is blue and neutral is slate; change them only as the design brief requires.
For an existing native app, refine its established components in scope; do not
copy a starter over the app or replace its architecture merely to polish a view.
For native color details read
[the color spec](../visual-design-modernization/references/color-system.md).
Verify the generated project with `swift build`, `swift test`, and
`swiftlint lint --strict --quiet`; report actual results rather than historical
template claims.

## Skill maintenance

When editing platform routing, ownership or gate rules, use
[eval-cases.md](references/eval-cases.md) to test observable decisions, including
native and legacy restraint cases.

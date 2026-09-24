# Basalt + Recharts web integration

Use this for React web scaffolds and migrations. Basalt owns UI primitives and
theme; the application still owns routing, authorization, data and business
logic. Official recipes are integration examples, not permission to add login
or other features absent from the requested product.

## Verify the installed release

Read the project's package/lock files, then the selected package's README,
`ai/INTEGRATION.md`, `ai/COMPATIBILITY.md`, `ai/RECIPES.md` and relevant declarations under
`node_modules/@nocoo/basalt/`. Use public entrypoints supported by that version.

At the 2026-09-21 check, npm published **2.1.7** while GitHub main declared
**2.1.8**. This is evidence of possible documentation skew, not a permanent
version pin. Check the current published release and peers when implementing;
GitHub main and the showcase can expose unreleased changes.

Current peer requirements: React/React DOM **19**, `lucide-react`; Recharts
**^3** for charts and Tailwind **^4** only for the Tailwind styling path.
Use the repository package manager and lockfile. If its stack or instructions
conflict, surface the required migration and obtain direction before broad
upgrades; do not bypass peers with `--force`/`--legacy-peer-deps`. The optional
table/date dependencies are not automatically required by built-in controls.

## One CSS entry

Choose exactly one path:

**Tailwind v4:** wire the framework's supported Tailwind integration. The
`@source` below is relative to a stylesheet in `src/`; adapt the path to the
actual file. Follow the installed release's import order:

```css
@source "../node_modules/@nocoo/basalt/dist/**/*.{js,jsx,ts,tsx}";
@import "@nocoo/basalt/styles/tailwind";
@import "tailwindcss";
```

**Standalone:** import `@nocoo/basalt/styles/standalone` in the application entry
(Next.js: root layout). This supplies Basalt tokens/control styles, **not a
global reset or arbitrary Tailwind utilities**. Supply app-owned page margin,
height, layout and box-sizing deliberately; scope additional CSS to app classes.

Do not load both modes or add the legacy scaffold's token CSS. Use Basalt token
utilities/CSS variables, checking their value format before composing colors.

## Providers and shell

Mount `ThemeProvider` once for the app. If an existing host owns theme, use the
supported controlled configuration and disable duplicate persistence/document
mutation. Align pre-hydration initialization with the provider's storage key and
default; Next.js interactive modules require a client boundary.

Use `LinkProvider` to map internal hrefs to the application's router; preserve
ordinary anchors for external URLs and mail/tel links. Mount required tooltip
and sidebar providers. Keep the existing URL/deep-link/back-state contract.

Use public components rather than a hand-built visual imitation:

| Public entrypoint | Typical imports |
|---|---|
| `@nocoo/basalt` | `Button`, `Input`, `LayerCard`, `ContentIsland`, `ThemeProvider`, `LinkProvider` |
| `@nocoo/basalt/components/app-shell` | `AppShell`, `AppMain`, `AppSkipLink` |
| `@nocoo/basalt/components/app-header` | `AppHeader` |
| `@nocoo/basalt/components/page-header` | `PageHeader` |
| `@nocoo/basalt/components/sidebar` | sidebar components/provider |
| `@nocoo/basalt/components/data-table` | `DataTable` and its public types |
| `@nocoo/basalt/charts/*` | supported chart wrappers and styling helpers |

These are starting points, not an exhaustive export guarantee: confirm the
installed declaration. Never import showcase-private modules or package `src/`.
Use responsive shell recipes as references, then supply real app navigation.
Retain named mobile navigation, focus restoration and the correct scroll owner.

## Recharts and data

Use Recharts 3 directly for custom charts or Basalt's public chart wrappers
where they fit. Share Basalt chart colors, tooltip/axis styling and legend
semantics. Give responsive charts a nonzero-height container and `min-width: 0`
inside flex/grid layouts; verify mobile and hidden-to-visible transitions.

The Basalt chart palette is separate from the control accent. Use exported
utilities or documented tokens; do not copy a second seed-generated palette.
Use explicit series descriptors, dates/units and accessible data alternatives.
Missing values remain missing; negative values and mixed currencies must retain
the application's meaning. No synthetic history or automatic API-error fixture
fallback. Explicit demo mode remains visibly marked and isolated from real data.

## Evidence and references

Build/typecheck using actual public imports; run affected interaction tests,
including navigation, filter restoration and privacy. Capture desktop/mobile
and relevant theme screenshots for the design gate. A dependency in package.json
alone does not count as a Basalt migration.

- [Official README](https://github.com/nocoo/basalt/blob/main/README.md)
- [Integration](https://github.com/nocoo/basalt/blob/main/INTEGRATION.md)
- [Compatibility](https://github.com/nocoo/basalt/blob/main/packages/basalt/ai/COMPATIBILITY.md)
- [Recipes](https://github.com/nocoo/basalt/blob/main/packages/basalt/ai/RECIPES.md)
- [Catalog](https://basaltui.com/ui) · [Banking](https://basaltui.com/banking) · [Portfolio](https://basaltui.com/portfolio)

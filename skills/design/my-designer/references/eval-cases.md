# Behavioral evals — routing, ownership and acceptance

Run these after changes to platform defaults, orchestration or gate rules.
Give an independent evaluator the skill and one realistic request/fixture below;
ask for concrete next actions, delegation contracts and delivery criteria.
Do not give it the expected outcome column before collecting its answer.
Use a read-only/dry-run evaluation unless implementation is explicitly in scope.

| Case / input fixture | Observable pass | Observable fail |
|---|---|---|
| **Web default:** “Build Financial's React asset app”; React 19, no UI kit | Actual Basalt public shell/controls, one provider/token authority, Recharts 3 charts; inspect release peers and exports | Copies custom seed templates, reimplements lookalikes, or only adds a dependency |
| **Whole app ownership:** four sections with shared filters and navigation | Lead owns shell/shared state; independent agents get bounded sections and same Basalt contract; lead integrates and tests journeys | One specialist gets the whole task and lead exits; independent palettes or broken cross-page paths |
| **Native restraint:** “Polish VoxPocket's macOS SwiftUI window” | Retains SwiftUI kit/native interactions; no React/Basalt/Recharts dependency | Converts native screen to a web stack solely because of web defaults |
| **Legacy opt-in:** “Use the old custom-seed Vite template, not Basalt” | Explicitly selects legacy template and one legacy theme; identifies it honestly | Refuses explicit user choice, or claims old custom components are Basalt |
| **No fake Basalt:** worker returns hand-built Sidebar/Card with Basalt-like CSS | Rejects as a Basalt migration; requests actual public library components and checks imports | Accepts visual resemblance/package.json alone as library integration |
| **Peer conflict:** React 18 locked by repository instructions | Reports React 19 requirement and scopes/requests direction for the necessary upgrade | `--force`, `--legacy-peer-deps`, or silently overrides repository instructions |
| **Release skew:** npm version trails GitHub main; a shown API is absent in installed declarations | Uses installed/public supported API or explicitly scopes an upgrade | Assumes main's API exists, imports package source/private showcase modules |
| **CSS choice:** existing app without Tailwind | Uses standalone alone and supplies host layout/reset intentionally | Loads both CSS modes or assumes standalone supplies all Tailwind utilities/global reset |
| **Theme conflict:** project already has theme persistence | Chooses one documented theme owner, keeps hydration consistent | Mounts competing global providers or legacy seed writer beside Basalt |
| **Palette handoff:** specialist sends its own purple gradient/token sheet | Maps/reworks result to the selected Basalt authority; retains chart/semantic identities | Accepts a second palette or replaces financial semantic colors with brand accent |
| **Real-data failure:** production balance endpoint returns 503 | Error/retry state; existing data mode and calculations preserved | Substitutes fixture balances, zeros, or invented history |
| **Financial workflow regression:** new page loses month→category→transaction drill-down | Preserves the path, filtering and back-state; checks privacy and currency meaning | Ships just a prettier overview or changes accounting to fit a chart |
| **Screenshot gate:** screenshots exist and author says “finished” | Reviewer gets north-star/screenshots; actual /35 and P0/P1 recorded; P0 fixed before delivery | Asks “looks good?” instead of review or fabricates a score |
| **Unavailable tool:** dataviz/Figma/reviewer absent | Discloses capability gap, uses available scoped fallback, marks missing review honestly | Pretends tool ran or installs unrelated tooling without authorization |
| **Scope restraint:** unrelated operational dashboard project | Defers to its own project workflow | Expands the four-project allowlist because the task says “dashboard” |

## Evaluation discipline

Score decisions and artifacts, not exact wording or counts of tool calls. A
small component polish need not invoke multiple specialists; a complete app
must still have clear lead ownership and integration. Use only available tools.

For a changed rule, compare the previous and updated skill on the same input
when useful. Report whether the update actually changed behavior; both passing
is regression coverage, not evidence of a behavioral improvement. Include the
native, legacy and scope restraint cases alongside the Web default so the new
default cannot accidentally become a universal framework rewrite.

Record actual evaluation outcomes in the task report. This case catalog is not
a claim that an evaluator has run, and structural validation alone does not
prove behavioral correctness.

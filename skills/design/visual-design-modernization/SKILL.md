---
name: visual-design-modernization
description: Use when a user says an app's UI "looks bad / dated / not modern" and wants to improve visual quality (spacing, typography, color, hierarchy, data-viz) — especially for SwiftUI/macOS/iOS but the method is framework-agnostic. Provides a repeatable diagnose→north-star→isolated-prototype→objective-review→migrate loop, a reusable design-reviewer that substitutes for design experience, and a swappable brand-color system. Works fully without Figma.
allowed-tools: Read, Write, Edit, Bash, Agent
---

# Visual Design Modernization

A repeatable method for taking a UI a user thinks is "ugly / not modern" and making it genuinely better — **for users who do not have design experience**. The core idea: replace missing design intuition with an **external, objective judge** (the `design-reviewer` agent) + a written **north-star** of concrete rules, and de-risk the work by prototyping in **isolation** before touching production code.

**Announce at start:** "I'm using the visual-design-modernization skill."

## When to use

- User says the UI "looks bad", "not modern", "dated", "单调/拥挤/难看", or wants "visual polish".
- User lacks design experience and wants tooling/skills to compensate — this is the primary case.
- Framework-agnostic in principle; the bundled code helpers target SwiftUI/macOS/iOS.

## When NOT to use

- Functional bugs, layout that's broken (not ugly) → normal engineering.
- User already has a designer / Figma source of truth they want implemented faithfully → use a design-to-code path instead.

## The core problem & the fix

A user without design experience cannot reliably tell *why* something looks bad or whether a change improved it. Don't ask them to. Instead:

1. **Externalize judgment** → the `design-reviewer` agent scores screenshots against an objective rubric.
2. **Write the target down** → a `north-star.md` turns "modern" into concrete, checkable rules.
3. **See it, don't imagine it** → render real screenshots every iteration (SwiftUI `ImageRenderer`), never trust code-reading for aesthetics.
4. **De-risk** → prototype in an isolated dir first; migrate to production only after the user approves the look.

## The loop

```
0. DIAGNOSE      screenshot the current UI → name concrete faults (not vibes)
1. NORTH-STAR    write/adapt north-star.md (references/north-star-template.md)
2. PROTOTYPE     build in an ISOLATED dir with mock data — do NOT touch
                 constitution-/token-locked production code yet
3. RENDER        ImageRenderer → PNG (references/swiftui-preview-snapshot.md)
4. REVIEW        design-reviewer agent scores it vs north-star → P0/P1 fixes
5. ITERATE       fix P0s, re-render, re-review until score clears the bar
6. USER GATE     show screenshots; user approves the direction
7. MIGRATE       only now change production code + tests (+ amend any
                 design "constitution" via its own governance/PR)
```

Never skip 3–4. Aesthetic claims must be verified against a rendered pixel, by the reviewer, not asserted from code.

### Step 0 — Diagnose (concrete, not vibes)

Get a screenshot of the current screen. Translate "ugly" into named, locatable faults tied to the rubric dimensions, e.g.:
- no max content width → cards stretched sparse across a wide window
- KPIs share one big card → no columnar separation
- zero data-viz → arrows only, "text report not a dashboard"
- flat cards → no elevation, glued to background
- one font size everywhere → no hierarchy

If you can't screenshot it, ask the user to paste one. **Do not proceed on code-reading alone.**

### Step 1 — North-star

Copy `references/north-star-template.md` into the project's `design/north-star.md` and fill it in. Anchor to concrete, public references (Linear, Vercel dashboard, Apple system apps) — **no Figma needed**. This file is what the reviewer scores against; keep every rule concrete and checkable (px values, font steps, color roles).

### Step 2 — Prototype in isolation (the de-risk move)

Production design systems are often guarded by a "constitution" doc + a wall of token-compliance tests. **Fighting those before the user has approved a look is wasted effort.** Instead:

- Build the new look in a fresh `Prototype/` dir with **mock data**.
- **First verify the compliance tests load sources by explicit filename, not directory glob** — if by glob, put the prototype outside the scanned tree. (In practice most load by explicit filename, so a sibling `Prototype/` dir is invisible to them.)
- Confirm isolation: production build + full test suite stay green with the prototype present → zero risk.

### Step 3 — Render (see it)

Use `ImageRenderer` in a throwaway executable that links the package. Key gotchas (full recipe in `references/swiftui-preview-snapshot.md`):
- `ScrollView` collapses to zero height under `ImageRenderer` → render an eager, non-scrolling variant (`.fixedSize(horizontal:false, vertical:true)`).
- `LazyVGrid` doesn't materialize offscreen → provide an eager `HStack`/`Grid` path for snapshots.
- Render light + dark, and each palette/seed variant.
- Copy PNGs into the repo (`design/prototype-shots/`) and `open` them so the user can actually see them.

### Step 4 — Objective review

Invoke the `design-reviewer` agent with the screenshot path(s) + the north-star path. It returns a 7-dimension score (/35) and prioritized P0/P1 fixes with concrete values. This is the step that substitutes for the user's missing design eye. Fix P0s, re-render, re-review.

> If a project-local `design-reviewer` file isn't yet registered as an agent in the running session, invoke a `general-purpose` agent and instruct it to follow the `design-reviewer.md` instructions verbatim (Read the file first). Same result.

### Step 5–6 — Iterate & user gate

Loop until the score clears the bar and P0s are gone. Then show the user the screenshots and get explicit approval on **direction** before any production change. Offer real choices (elevation style, grey palette, brand color) as side-by-side rendered variants, not verbal descriptions.

### Step 7 — Migrate to production

Only after approval:
- If a design "constitution" governs the tokens, amend it via its own process (PR + version bump + migration note) — the constitution is usually the real blocker (it may forbid shadows, colored fills, multi-level type, new card types).
- Port the prototype tokens/components into production views.
- Update the token-compliance tests to the new values in the same PR.
- Keep the isolated prototype building until the migration lands.

## What "modern" concretely means (portable checklist)

The reviewer enforces these; they're the recurring wins:
- **Max content width** (~1100–1280pt) centered — kills "stretched sparse".
- **Independent KPI cards** in a responsive grid — kills "numbers floating in one bar".
- **Data-viz next to numbers** — sparkline (area+line), ring gauge for ratios. A dashboard with only ↑↓ arrows reads as a text report.
- **Elevation** — either soft shadow *or* pew-style flat luminance tiers (L0 bg < L1 card < L2 inner); pick one, be consistent.
- **≥3 type levels** on one screen (display / body / meta) + rounded design for numbers.
- **Status as colored pills**, not grey text (`color.opacity(0.12–0.20)` fill + full-saturation text, `Capsule`).
- **Restrained color** — semantic system colors, no hex hardcode; ≤1 accent anchor per card.
- **Hued-but-restrained greys** (Radix slate) or **pure neutral** (Tailwind neutral); avoid heavy single-hue greys that read "cheap".

## Color: a swappable brand system

Give the app one `seed` color and derive the whole primary token set (primary / hover / active / subtle / muted / border / text / onPrimary / ring) with `makePrimaryPalette(seed:isDark:)`. Swapping the seed re-themes the app; **semantic colors (success/warning/danger) stay fixed** so "green=good/red=bad" never breaks. Full implementation + palettes in `references/color-system.md`.

Two modes coexist on macOS: follow the system accent color, or pin a brand seed — both feed the same derivation pipeline.

## Deliverables this skill produces

- `design/north-star.md` — the project's visual target (from template).
- `Prototype/` — isolated, mock-data prototype (SwiftUI) with `#Preview`s.
- `design/prototype-shots/` — rendered PNGs (light/dark, variants).
- Objective reviewer scores guiding each iteration.
- (On approval) production migration PR + constitution amendment.

## Anti-patterns

- ❌ Judging aesthetics from code without rendering.
- ❌ Editing production, constitution-locked code before the user approves the look.
- ❌ Asking a design-inexperienced user "does this look good?" without giving them rendered options and an objective score to anchor on.
- ❌ Adding shadows/tints/type-levels that the design constitution forbids without amending it → breaks the compliance test wall.
- ❌ Hardcoding hex where a semantic/system color exists.

## References

- `references/north-star-template.md` — fill-in visual-target rules.
- `references/color-system.md` — `makePrimaryPalette` + Radix slate / Tailwind neutral / Apple system color values.
- `references/swiftui-preview-snapshot.md` — ImageRenderer snapshot recipe + gotchas.
- `references/design-reviewer-rubric.md` — the 7-dimension scoring rubric (shared with the global `design-reviewer` agent).

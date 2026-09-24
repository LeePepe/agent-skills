# Color System (SwiftUI)

Two independent parts, both reusable across apps:
1. **Neutral palette** — the greys/backgrounds (choose Radix slate or Tailwind neutral).
2. **Brand primary** — derived from a single `seed` color via `makePrimaryPalette`.

Semantic colors (success/warning/danger) are **fixed** (Apple system colors) so swapping the
brand seed never breaks "green=good / red=bad".

---

## 1. Neutral palettes (exact hex)

Heavy single-hue greys read "cheap". Use a calibrated scale. Two good choices:

### Radix slate (slight cool cast — recommended default)
```
LIGHT                         DARK
bg L0     #F9F9FB (slate2)    #111113 (slateDark1)
card L1   #FFFFFF             #18191B (slateDark2)
inner L2  #F0F0F3 (slate3)    #212225 (slateDark3)
text 1°   #1C2024 (slate12)   #EDEEF0 (slateDark12)
text 2°   #60646C (slate11)   #B0B4BA (slateDark11)
text 3°   #80838D (slate10)   #777B84 (slateDark10)
border    #D9D9E0 (slate6)    #363A3F (slateDark6)
```

### Tailwind neutral (pure grey, hue 0 — maximally neutral)
```
LIGHT                    DARK
bg L0     #FAFAFA        #171717
card L1   #FFFFFF        #262626
inner L2  #F5F5F5        #2E2E2E
text 1°   #171717        #FAFAFA
text 2°   #525252        #A3A3A3
text 3°   #737373        #737373
border    #E5E5E5        #404040
```

Light-mode difference between the two is subtle; dark-mode is where character shows
(slate = deep blue-black, neutral = pure black-grey). Render both and let the user pick.

Flat elevation: L0 < L1 < L2 luminance + 1px `border`. Soft elevation: drop the border, add shadow.

## 2. Semantic colors — Apple system (fixed)
```
             LIGHT      DARK
success   #34C759    #30D158   (systemGreen)
warning   #FF9500    #FF9F0A   (systemOrange)
danger    #FF3B30    #FF453A   (systemRed)
```
In SwiftUI you can also just use `Color.green/.orange/.red` — on macOS they resolve to these
and auto-adapt to appearance. Hardcode hex only when you need exact control.

## 3. Brand primary — one seed → whole token set

`makePrimaryPalette(seed:isDark:)` derives the full primary token set from a single color using
HSB + WCAG on-color choice. Token semantics mirror Radix (9=solid, 10=hover, 3=subtle, 7=ring,
11=text), shadcn (`primary` / `primary-foreground` / `ring`), and Material (container/onContainer).
Rationale: don't port Material's HCT (too heavy) or pre-generate Radix's 12-step scale (needs a
toolchain) — HSB derivation is standard-library-only and good enough for a flat dashboard.

### Preset seeds (Radix step-9, calibrated)
```
blue   #0090FF  (neutral/professional/data)
purple #8E4EC6  (creative/AI)
teal   #12A594  (health/finance)
orange #F76B15  (alert/energy)
appleBlue #007AFF (Apple systemBlue)
```

### Implementation

```swift
import SwiftUI
#if canImport(AppKit)
import AppKit
#endif

extension Color {
    init(hex: String) {
        let s = hex.trimmingCharacters(in: CharacterSet(charactersIn: "#"))
        var v: UInt64 = 0; Scanner(string: s).scanHexInt64(&v)
        let r = Double((v >> 16) & 0xFF) / 255
        let g = Double((v >> 8) & 0xFF) / 255
        let b = Double(v & 0xFF) / 255
        self.init(.sRGB, red: r, green: g, blue: b, opacity: 1)
    }
}

struct PrimaryPalette: Sendable {
    let primary, primaryHover, primaryActive: Color
    let primarySubtle, primaryMuted, primaryBorder: Color
    let primaryText, onPrimary, onPrimarySubtle, ring: Color
}

private func hsbComponents(_ c: Color) -> (h: Double, s: Double, b: Double) {
    #if canImport(AppKit)
    let ns = NSColor(c).usingColorSpace(.deviceRGB) ?? .black
    var h: CGFloat = 0, s: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
    ns.getHue(&h, saturation: &s, brightness: &b, alpha: &a)
    return (Double(h), Double(s), Double(b))
    #else
    return (0.58, 0.8, 0.9)
    #endif
}
func hsbHue(_ c: Color) -> Double { hsbComponents(c).h }

private func relLuminance(_ c: Color) -> Double {
    #if canImport(AppKit)
    let ns = NSColor(c).usingColorSpace(.sRGB) ?? .black
    func lin(_ v: CGFloat) -> Double {
        let x = Double(v); return x <= 0.03928 ? x/12.92 : pow((x+0.055)/1.055, 2.4)
    }
    return 0.2126*lin(ns.redComponent) + 0.7152*lin(ns.greenComponent) + 0.0722*lin(ns.blueComponent)
    #else
    return 0.5
    #endif
}
// WCAG: choose black/white foreground by which gives higher contrast.
private func contrastChoose(_ bg: Color) -> Color {
    let L = relLuminance(bg)
    return (1.05 / (L + 0.05)) >= ((L + 0.05) / 0.05) ? .white : .black
}
private func clamp(_ x: Double) -> Double { min(1, max(0, x)) }

func makePrimaryPalette(seed: Color, isDark: Bool) -> PrimaryPalette {
    let (h, s, b) = hsbComponents(seed)
    func c(_ h: Double, _ s: Double, _ b: Double) -> Color {
        Color(hue: h, saturation: clamp(s), brightness: clamp(b))
    }
    if isDark {
        // dark: hover brightens, subtle/muted darken, text lightens (Radix-dark behavior)
        let primary = c(h, s - 0.05, b + 0.06)
        return PrimaryPalette(
            primary: primary,
            primaryHover:  c(h, s, b + 0.08),
            primaryActive: c(h, s, b + 0.14),
            primarySubtle: c(h, s * 0.45, 0.18),
            primaryMuted:  c(h, s * 0.50, 0.26),
            primaryBorder: c(h, s * 0.55, 0.36),
            primaryText:   c(h, s * 0.70, b + 0.28),
            onPrimary:     contrastChoose(primary),
            onPrimarySubtle: c(h, s * 0.70, b + 0.28),
            ring: primary.opacity(0.65))
    } else {
        let primary = seed
        return PrimaryPalette(
            primary: primary,
            primaryHover:  c(h, s, b - 0.08),
            primaryActive: c(h, s, b - 0.14),
            primarySubtle: c(h, s * 0.18, 0.97),
            primaryMuted:  c(h, s * 0.40, 0.90),
            primaryBorder: c(h, s * 0.55, 0.80),
            primaryText:   c(h, min(1, s + 0.10), b - 0.20),
            onPrimary:     contrastChoose(primary),
            onPrimarySubtle: c(h, min(1, s + 0.10), b - 0.20),
            ring: primary.opacity(0.55))
    }
}
```

### On-brand chart palette (same hue family as the seed)
```swift
func chartPalette(seed: Color, isDark: Bool) -> [Color] {
    let seedHue = hsbHue(seed) * 360
    let offsets: [Double] = [0, -15, 40, 95, 130, 175, -70, 210]  // walk the wheel from seed
    return offsets.map { off in
        let h = ((seedHue + off).truncatingRemainder(dividingBy: 360) + 360)
            .truncatingRemainder(dividingBy: 360) / 360
        return isDark ? Color(hue: h, saturation: 0.66, brightness: 0.82)
                      : Color(hue: h, saturation: 0.72, brightness: 0.62)
    }
}
```

## 4. Follow-system vs pinned brand (macOS)

```swift
enum ThemeMode { case followSystem; case brand(Color) }
```
- `.followSystem`: seed = `Color.accentColor` (or `NSColor.controlAccentColor`), re-derive on
  `effectiveAppearance` / `NSColor.systemColorsDidChangeNotification` changes.
- `.brand(seed)`: pin a constant. Recommended default for dashboards (consistent, controllable
  contrast; a user's system accent could be graphite/red and clash with chart semantics).
- Both feed the same `makePrimaryPalette` pipeline — only the seed source differs.

Optional upgrade: swap HSB for OKLCH (~60 lines) for perceptually-even subtle/hover steps across
all hues. Not needed for a flat dashboard.

# SwiftUI Preview → PNG Snapshot Recipe

You must **see** the UI to judge it. `swift build` doesn't render previews. Use `ImageRenderer`
in a throwaway executable that links the package. This lets you render every variant
(light/dark, palette, brand seed) to PNGs the user can open — the Figma-free feedback loop.

## The throwaway snapshot package

```bash
mkdir -p /tmp/protoshot/Sources/protoshot
cat > /tmp/protoshot/Package.swift <<'EOF'
// swift-tools-version: 6.2
import PackageDescription
let package = Package(
    name: "protoshot",
    platforms: [.macOS(.v26)],   // match your package's min OS
    dependencies: [ .package(path: "/ABS/PATH/TO/YourUIPackage") ],
    targets: [ .executableTarget(name: "protoshot",
        dependencies: [ .product(name: "YourUIPackage", package: "YourUIPackage") ]) ]
)
EOF
```

```swift
// /tmp/protoshot/Sources/protoshot/main.swift
import SwiftUI
import AppKit
import YourUIPackage

@MainActor
func snapshot(isDark: Bool, path: String, @ViewBuilder _ content: () -> some View) {
    let view = content()
        .environment(\.colorScheme, isDark ? .dark : .light)
    let r = ImageRenderer(content: view)
    r.scale = 2.0                                   // retina
    guard let img = r.nsImage, let tiff = img.tiffRepresentation,
          let rep = NSBitmapImageRep(data: tiff),
          let png = rep.representation(using: .png, properties: [:]) else {
        print("FAIL \(path)"); return
    }
    try? png.write(to: URL(fileURLWithPath: path))
    print("WROTE \(path) \(img.size)")
}

MainActor.assumeIsolated {
    snapshot(isDark: false, path: "/tmp/protoshot/light.png") {
        YourPageView(scrollable: false).frame(width: 1280)
            .fixedSize(horizontal: false, vertical: true)
    }
    snapshot(isDark: true, path: "/tmp/protoshot/dark.png") {
        YourPageView(scrollable: false).frame(width: 1280)
            .fixedSize(horizontal: false, vertical: true)
    }
}
```

```bash
cd /tmp/protoshot && swift run 2>&1 | grep -E "WROTE|FAIL|error:"
# copy into the repo so the user can open them:
cp /tmp/protoshot/*.png /ABS/PATH/TO/repo/design/prototype-shots/
open /ABS/PATH/TO/repo/design/prototype-shots/light.png
```

Then Read the PNG in your own context to review it, and/or hand the path to `design-reviewer`.

## Gotchas (these will bite)

1. **ScrollView collapses to zero height** under `ImageRenderer` (it proposes unbounded height →
   content lays out offscreen → blank PNG). Give your page a `scrollable: Bool` init and render
   the **non-scrolling** eager variant for snapshots:
   ```swift
   Group { if scrollable { ScrollView { content } } else { content } }
   ```
   Then `.fixedSize(horizontal: false, vertical: true)` so it reports true height.

2. **`LazyVGrid` doesn't materialize offscreen rows** under ImageRenderer. Provide an eager path
   (plain `HStack`/`Grid`) for snapshots:
   ```swift
   if lazy { LazyVGrid(...) { ... } } else { HStack(spacing: 16) { ... } }
   ```
   Pass `lazy: scrollable`.

3. **Blank/zero-height PNG** = symptom of (1) or (2). Check the printed `img.size` — if height is
   ~the frame height with no content, it collapsed.

4. **`public` for snapshot access.** Any type/enum used in the page view's `public init` default
   args must itself be `public` (e.g. `ProtoElevationMode`, `ProtoPalette`, `BrandSeed`), or the
   package won't compile against the external snapshot target.

5. **Strict concurrency:** enums stored in `EnvironmentKey.defaultValue` need `: Sendable`.

6. **Stale incremental build** in the snapshot package after you add files to the UI package:
   `rm -rf /tmp/protoshot/.build && swift run` (a targeted `rm` of derived files can delete needed
   `resource_bundle_accessor.swift` — full clean is safest).

7. **Downloads may be sandbox-restricted** for the shell — copy PNGs into the repo tree instead,
   and `open` from there.

## Isolation check (do this before prototyping)

Confirm the token-compliance tests load sources by explicit filename (not directory glob), so a
sibling `Prototype/` dir is invisible to them:
```bash
grep -n "contentsOfDirectory\|enumerator\|subpaths\|Glob\|sourceFile(named" Tests/**/*Compliance*.swift
```
If they enumerate a directory, put the prototype outside that tree. Then prove zero risk:
`swift build && swift test` stay green with the prototype present.

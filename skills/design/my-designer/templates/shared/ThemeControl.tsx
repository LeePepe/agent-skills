"use client";
import { useEffect, useState } from "react";
import { SEEDS, type SeedName, type NeutralName } from "./color-system";
import { applyTheme, getSeed, getNeutral, getMode, type Mode } from "./theme";
import { cn } from "./utils";

/**
 * ThemeControl — swap seed / neutral / mode at runtime. This is the whole
 * "swappable brand" story: a brand is just a seed of the one design language.
 */
export function ThemeControl({ className }: { className?: string }) {
  const [seed, setSeed] = useState<SeedName>("blue");
  const [neutral, setNeutral] = useState<NeutralName>("slate");
  const [mode, setMode] = useState<Mode>("system");

  useEffect(() => {
    setSeed(getSeed());
    setNeutral(getNeutral());
    setMode(getMode());
  }, []);

  function pickSeed(s: SeedName) {
    applyTheme(s, neutral, mode);
    setSeed(s);
  }
  function toggleNeutral() {
    const n: NeutralName = neutral === "slate" ? "neutral" : "slate";
    applyTheme(seed, n, mode);
    setNeutral(n);
  }
  function cycleMode() {
    const order: Mode[] = ["system", "light", "dark"];
    const m = order[(order.indexOf(mode) + 1) % order.length];
    applyTheme(seed, neutral, m);
    setMode(m);
  }

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="flex items-center gap-1.5">
        {(Object.keys(SEEDS) as SeedName[]).map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => pickSeed(s)}
            title={s}
            className={cn(
              "size-5 rounded-full border transition-transform",
              seed === s ? "scale-110 ring-2 ring-offset-1 ring-ring" : "opacity-70 hover:opacity-100",
            )}
            style={{ background: SEEDS[s], borderColor: "var(--border)" }}
          />
        ))}
      </div>
      <button
        type="button"
        onClick={toggleNeutral}
        className="rounded-[var(--radius-inner)] border border-border px-2 py-1 text-xs capitalize hover:bg-inner"
      >
        {neutral}
      </button>
      <button
        type="button"
        onClick={cycleMode}
        className="rounded-[var(--radius-inner)] border border-border px-2 py-1 text-xs capitalize hover:bg-inner"
      >
        {mode}
      </button>
    </div>
  );
}

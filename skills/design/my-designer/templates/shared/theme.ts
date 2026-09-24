/**
 * Theme runtime — applies the seed color system to the DOM.
 * Framework-agnostic; works in Vite and Next (client).
 *
 * A "theme" here = (seed, neutral, mode). Changing the seed re-themes the whole
 * app — there is no notion of separate brands, only seeds of one design language.
 */
import { buildTokens, SEEDS, type SeedName, type NeutralName } from "./color-system";

export type Mode = "light" | "dark" | "system";

const SEED_KEY = "ds-seed";
const NEUTRAL_KEY = "ds-neutral";
const MODE_KEY = "ds-mode";

function root(): HTMLElement | null {
  return typeof document === "undefined" ? null : document.documentElement;
}

function systemDark(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function resolveDark(mode: Mode): boolean {
  return mode === "system" ? systemDark() : mode === "dark";
}

export function getSeed(): SeedName {
  if (typeof localStorage === "undefined") return "blue";
  const s = localStorage.getItem(SEED_KEY) as SeedName | null;
  return s && s in SEEDS ? s : "blue";
}

export function getNeutral(): NeutralName {
  if (typeof localStorage === "undefined") return "slate";
  return (localStorage.getItem(NEUTRAL_KEY) as NeutralName | null) ?? "slate";
}

export function getMode(): Mode {
  if (typeof localStorage === "undefined") return "system";
  return (localStorage.getItem(MODE_KEY) as Mode | null) ?? "system";
}

/** Apply (seed, neutral, mode) → CSS variables + .dark class. Persists choices. */
export function applyTheme(
  seed: SeedName = getSeed(),
  neutral: NeutralName = getNeutral(),
  mode: Mode = getMode(),
): void {
  const el = root();
  if (!el) return;
  const isDark = resolveDark(mode);
  const vars = buildTokens(SEEDS[seed], neutral, isDark);
  for (const [k, v] of Object.entries(vars)) el.style.setProperty(k, v);
  el.classList.toggle("dark", isDark);
  localStorage.setItem(SEED_KEY, seed);
  localStorage.setItem(NEUTRAL_KEY, neutral);
  localStorage.setItem(MODE_KEY, mode);
}

/** Hydrate from storage on boot. */
export function initTheme(): { seed: SeedName; neutral: NeutralName; mode: Mode } {
  const seed = getSeed();
  const neutral = getNeutral();
  const mode = getMode();
  applyTheme(seed, neutral, mode);
  return { seed, neutral, mode };
}

/** Inline in <head> to prevent theme flash before hydration. */
export const NO_FLASH_SCRIPT = `(function(){try{
  var m=localStorage.getItem("${MODE_KEY}")||"system";
  var d=m==="dark"||(m==="system"&&matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.classList.toggle("dark",d);
}catch(e){}})();`;

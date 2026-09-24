"use client";
import { useEffect } from "react";
import { initTheme } from "../shared/theme";

/** Applies the full seed token set on the client after the no-flash script. */
export function ThemeInit() {
  useEffect(() => {
    initTheme();
  }, []);
  return null;
}

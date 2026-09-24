import type { Metadata } from "next";
import "./globals.css";
import { NO_FLASH_SCRIPT } from "../shared/theme";
import { ThemeInit } from "./ThemeInit";

export const metadata: Metadata = {
  title: "Design System — Next.js",
  description: "One design language, seed-themed",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: NO_FLASH_SCRIPT }} />
      </head>
      <body>
        <ThemeInit />
        {children}
      </body>
    </html>
  );
}

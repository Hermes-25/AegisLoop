import type { Metadata } from "next";
import "@fontsource-variable/inter";
import "@fontsource-variable/jetbrains-mono";
import "./globals.css";

import { AppShell } from "@/components/app-shell";

export const metadata: Metadata = {
  title: { default: "AegisLoop Command Center", template: "%s · AegisLoop" },
  description: "A closed-loop adversarial threat lab for emerging payment fraud.",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body>
        <a
          href="#main-content"
          className="fixed left-4 top-3 z-[100] -translate-y-20 rounded-md bg-[var(--signal-orange)] px-4 py-2 font-semibold text-[var(--on-orange)] focus:translate-y-0"
        >
          Skip to content
        </a>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}

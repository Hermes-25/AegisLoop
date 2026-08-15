"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BookOpen,
  Crosshair,
  Database,
  FlaskConical,
  Gauge,
  Menu,
  Radar,
  ShieldCheck,
  Swords,
  X,
} from "lucide-react";

import { HealthIndicator } from "@/components/health-indicator";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navigation = [
  { href: "/", label: "Mission briefing", icon: Gauge },
  { href: "/identify", label: "Identify", icon: Radar },
  { href: "/generate", label: "Generate", icon: FlaskConical },
  { href: "/adapt", label: "Adapt", icon: Swords },
  { href: "/defend", label: "Defend", icon: ShieldCheck },
  { href: "/reality-check", label: "Reality check", icon: Activity },
  { href: "/evidence", label: "Evidence", icon: Database },
  { href: "/benchmark", label: "Live benchmark", icon: Crosshair },
  { href: "/methodology", label: "Methodology", icon: BookOpen },
];

function Mark() {
  return (
    <div className="relative grid h-9 w-9 place-items-center rounded-md border border-[rgb(255_122_61_/_0.55)] bg-[rgb(255_122_61_/_0.08)]" aria-hidden="true">
      <span className="absolute h-4 w-4 rounded-full border-2 border-[var(--signal-orange)]" />
      <span className="absolute h-6 w-6 rotate-45 border-r border-t border-[var(--accent-blue)]" />
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[232px_1fr]">
      {open && <button aria-label="Close navigation overlay" className="fixed inset-0 z-40 bg-black/60 lg:hidden" onClick={() => setOpen(false)} />}
      <aside className={cn("fixed inset-y-0 left-0 z-50 flex w-[272px] -translate-x-full flex-col border-r border-[var(--border)] bg-[var(--chrome)] transition-transform lg:w-[232px] lg:translate-x-0", open && "translate-x-0")}>
        <div className="flex h-20 items-center justify-between border-b border-[var(--border)] px-5">
          <Link href="/" className="flex items-center gap-3" onClick={() => setOpen(false)}>
            <Mark />
            <div><span className="block text-sm font-bold tracking-[0.08em]">AEGISLOOP</span><span className="block text-[0.62rem] uppercase tracking-[0.18em] text-[var(--text-muted)]">Threat laboratory</span></div>
          </Link>
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setOpen(false)} aria-label="Close navigation"><X className="h-5 w-5" /></Button>
        </div>
        <nav aria-label="Primary" className="scrollbar-thin flex-1 overflow-y-auto px-3 py-5">
          <p className="eyebrow px-3 pb-3">Closed-loop stages</p>
          <ul className="space-y-1">
            {navigation.map(({ href, label, icon: Icon }) => {
              const active = href === "/" ? pathname === href : pathname.startsWith(href);
              return (
                <li key={href}>
                  <Link href={href} onClick={() => setOpen(false)} aria-current={active ? "page" : undefined} className={cn("group flex min-h-11 items-center gap-3 rounded-md border-l-2 px-3 text-sm transition-colors", active ? "border-[var(--signal-orange)] bg-[var(--surface-raised)] font-semibold text-[var(--text)]" : "border-transparent text-[var(--text-secondary)] hover:bg-[var(--surface)] hover:text-[var(--text)]")}>
                    <Icon className={cn("h-4 w-4", active ? "text-[var(--signal-orange)]" : "text-[var(--text-muted)] group-hover:text-[var(--accent-blue)]")} aria-hidden="true" />{label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        <div className="border-t border-[var(--border)] p-4"><HealthIndicator /></div>
      </aside>
      <div className="min-w-0 lg:col-start-2">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-[var(--border)] bg-[rgb(8_19_33_/_0.92)] px-4 backdrop-blur-md sm:px-6 lg:px-8">
          <div className="flex items-center gap-3"><Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setOpen(true)} aria-label="Open navigation"><Menu className="h-5 w-5" /></Button><span className="eyebrow hidden sm:block">Mastercard Innovation Challenge 2026</span></div>
          <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]"><span className="hidden sm:inline">Synthetic-only environment</span><span className="h-1.5 w-1.5 rounded-full bg-[var(--defender)]" aria-hidden="true" /><span>Offline lab</span></div>
        </header>
        <main id="main-content" className="mx-auto w-full max-w-[1440px] px-4 py-8 sm:px-6 lg:px-8 lg:py-10">{children}</main>
      </div>
    </div>
  );
}

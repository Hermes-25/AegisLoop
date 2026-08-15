"use client";

import { DatabaseZap, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <section className="mx-auto mt-16 max-w-2xl rounded-[var(--radius)] border border-[var(--critical)] bg-[var(--surface)] p-8"><DatabaseZap className="h-9 w-9 text-[var(--critical)]" /><p className="eyebrow mt-6 !text-[var(--critical)]">Evidence unavailable</p><h1 className="mt-3 text-2xl font-semibold">This view stopped before rendering an unverified claim.</h1><p className="mt-4 text-sm leading-6 text-[var(--text-secondary)]">{error.message || "A required artifact is missing or malformed."}</p>{error.digest && <p className="mono mt-3 text-xs text-[var(--text-muted)]">Reference: {error.digest}</p>}<Button onClick={reset} className="mt-6"><RotateCcw className="h-4 w-4" />Retry validation</Button></section>;
}

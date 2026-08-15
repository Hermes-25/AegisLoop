"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, CircleDashed, ShieldAlert } from "lucide-react";

type Health = { status: "loading" | "ready" | "degraded"; count?: number };

export function HealthIndicator() {
  const [health, setHealth] = useState<Health>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 8_000);
    fetch("/api/health", { cache: "no-store", signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error("Health check failed");
        return response.json() as Promise<{ status: "ready"; artifacts: unknown[] }>;
      })
      .then((result) => setHealth({ status: result.status, count: result.artifacts.length }))
      .catch(() => setHealth({ status: "degraded" }))
      .finally(() => window.clearTimeout(timer));
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, []);

  if (health.status === "loading") {
    return <span className="flex items-center gap-2 text-xs text-[var(--text-muted)]"><CircleDashed className="h-3.5 w-3.5 animate-spin" />Validating evidence</span>;
  }
  if (health.status === "degraded") {
    return <span className="flex items-center gap-2 text-xs font-medium text-[var(--critical)]"><ShieldAlert className="h-3.5 w-3.5" />Evidence unavailable</span>;
  }
  return <span className="flex items-center gap-2 text-xs font-medium text-[var(--defender)]"><CheckCircle2 className="h-3.5 w-3.5" />Evidence ready · <span className="mono">{health.count}</span> validated artifacts</span>;
}

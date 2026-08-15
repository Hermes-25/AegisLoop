import * as React from "react";
import { cn } from "@/lib/utils";

export function Badge({ className, tone = "neutral", ...props }: React.ComponentProps<"span"> & { tone?: "neutral" | "orange" | "blue" | "green" | "amber" | "red" }) {
  const tones = {
    neutral: "border-[var(--border)] bg-[var(--surface-raised)] text-[var(--text-secondary)]",
    orange: "border-[rgb(255_122_61_/_0.45)] bg-[rgb(255_122_61_/_0.1)] text-[var(--signal-orange)]",
    blue: "border-[rgb(76_155_232_/_0.45)] bg-[rgb(76_155_232_/_0.1)] text-[var(--accent-blue)]",
    green: "border-[rgb(77_212_172_/_0.45)] bg-[rgb(77_212_172_/_0.1)] text-[var(--defender)]",
    amber: "border-[rgb(248_195_92_/_0.45)] bg-[rgb(248_195_92_/_0.1)] text-[var(--warning)]",
    red: "border-[rgb(255_107_107_/_0.45)] bg-[rgb(255_107_107_/_0.1)] text-[var(--critical)]",
  };
  return <span className={cn("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.08em]", tones[tone], className)} {...props} />;
}

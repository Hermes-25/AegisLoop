import { AlertTriangle, CheckCircle2, Info } from "lucide-react";
import { cn } from "@/lib/utils";

export function Alert({ title, children, tone = "info", className }: { title: string; children: React.ReactNode; tone?: "info" | "warning" | "success"; className?: string }) {
  const Icon = tone === "warning" ? AlertTriangle : tone === "success" ? CheckCircle2 : Info;
  const tones = { info: "border-[var(--accent-blue)]", warning: "border-[var(--warning)]", success: "border-[var(--defender)]" };
  return (
    <aside className={cn("flex gap-3 rounded-md border-l-4 bg-[var(--surface-raised)] p-4", tones[tone], className)}>
      <Icon className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
      <div><p className="font-semibold">{title}</p><div className="mt-1 text-sm leading-6 text-[var(--text-secondary)]">{children}</div></div>
    </aside>
  );
}

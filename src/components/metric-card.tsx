import { Card, CardContent } from "@/components/ui/card";
import { ProvenanceChip } from "@/components/provenance-chip";

export function MetricCard({ label, value, detail, source, field, tone = "orange" }: { label: string; value: string; detail: string; source: string; field: string; tone?: "orange" | "blue" | "green" | "amber" }) {
  const tones = { orange: "text-[var(--signal-orange)]", blue: "text-[var(--accent-blue)]", green: "text-[var(--defender)]", amber: "text-[var(--warning)]" };
  return <Card><CardContent><div className="flex items-start justify-between gap-3"><p className="text-sm font-medium text-[var(--text-secondary)]">{label}</p><ProvenanceChip source={source} field={field} /></div><p className={`mono mt-5 text-3xl font-semibold tracking-tight ${tones[tone]}`}>{value}</p><p className="mt-3 text-sm leading-6 text-[var(--text-muted)]">{detail}</p></CardContent></Card>;
}

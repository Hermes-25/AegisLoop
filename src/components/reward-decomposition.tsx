import type { DiagnosticRow } from "@/lib/evidence/schemas";
import { format } from "@/lib/format";

const definitions = [
  ["Approved value", "value_term"],
  ["Evasion", "evasion_term"],
  ["Detection cost", "detection_cost_term"],
  ["Resource cost", "resource_cost_term"],
  ["Novelty", "novelty_term"],
] as const;

export function RewardDecomposition({ rows }: { rows: DiagnosticRow[] }) {
  const means = definitions.map(([label, field]) => ({ label, field, value: rows.reduce((sum, row) => sum + row[field], 0) / rows.length }));
  const scale = Math.max(...means.map((term) => Math.abs(term.value)), 0.001);
  const fidelity = rows.reduce((sum, row) => sum + row.fidelity, 0) / rows.length;
  const reward = rows.reduce((sum, row) => sum + row.reward, 0) / rows.length;
  return <div><div className="rounded-md border border-[var(--border)] bg-[var(--chrome)] p-4 text-center"><p className="mono text-sm leading-7"><span className="text-[var(--signal-orange)]">R pre-fidelity</span> = value + evasion + detection cost + resource cost + novelty</p><p className="mono mt-1 text-sm"><span className="text-[var(--defender)]">R final</span> = R pre-fidelity × fidelity</p></div><div className="mt-5 space-y-4">{means.map((term) => <div key={term.field} className="grid grid-cols-[120px_1fr_70px] items-center gap-3"><span className="text-xs text-[var(--text-secondary)]">{term.label}</span><div className="relative h-3 rounded-full bg-[var(--chrome)]"><div className={`absolute top-0 h-3 rounded-full ${term.value < 0 ? "right-1/2 bg-[var(--critical)]" : "left-1/2 bg-[var(--signal-orange)]"}`} style={{ width: `${Math.abs(term.value) / scale * 48}%` }} /><span className="absolute left-1/2 top-[-3px] h-[18px] w-px bg-[var(--border)]" /></div><span className="mono text-right text-xs">{format.number(term.value)}</span></div>)}</div><div className="mt-6 grid gap-3 sm:grid-cols-2"><div className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] p-4"><p className="text-xs text-[var(--text-muted)]">Mean fidelity multiplier</p><p className="mono mt-2 text-xl text-[var(--defender)]">× {format.number(fidelity)}</p></div><div className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] p-4"><p className="text-xs text-[var(--text-muted)]">Mean final reward</p><p className="mono mt-2 text-xl text-[var(--text)]">{format.number(reward)}</p></div></div><p className="mt-4 text-xs leading-5 text-[var(--text-muted)]">At V2, approved value, evasion and novelty are zero in every diagnostic row. Only detection and resource costs remain; fidelity scales their sum.</p></div>;
}

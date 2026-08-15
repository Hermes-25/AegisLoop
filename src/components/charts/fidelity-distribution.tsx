"use client";

import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";
import type { DiagnosticRow } from "@/lib/evidence/schemas";
import { format } from "@/lib/format";

export function FidelityDistribution({ rows }: { rows: DiagnosticRow[] }) {
  const seeds = [...new Set(rows.map((row) => row.seed))];
  const points = rows.map((row) => ({ fidelity: row.fidelity, seedIndex: seeds.indexOf(row.seed), seed: row.seed }));

  return (
    <div>
      <div className="h-[300px] w-full" aria-hidden="true">
        <ResponsiveContainer>
          <ScatterChart accessibilityLayer={false} margin={{ top: 10, right: 18, bottom: 24, left: 14 }}>
            <CartesianGrid stroke="#20364f" vertical={false} />
            <XAxis type="number" dataKey="fidelity" domain={["dataMin - 0.01", 1]} tickFormatter={(value) => format.number(value, 2)} tick={{ fill: "#91a5ba", fontSize: 11 }} label={{ value: "Fidelity score", position: "bottom", fill: "#91a5ba", fontSize: 11 }} />
            <YAxis type="number" dataKey="seedIndex" domain={[-0.5, seeds.length - 0.5]} ticks={seeds.map((_, index) => index)} tickFormatter={(value) => String(seeds[value] ?? "")} tick={{ fill: "#91a5ba", fontSize: 10 }} width={76} />
            <Tooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={{ background: "#0b1a2c", border: "1px solid #2a425e", borderRadius: 8 }} formatter={(value, name) => name === "fidelity" ? [format.number(Number(value)), "Fidelity"] : [value, name]} />
            <Scatter data={points} fill="#ff7a3d" fillOpacity={0.55} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-xs">
          <caption className="sr-only">V2 fidelity summary by seed</caption>
          <thead className="text-[var(--text-muted)]"><tr className="border-b border-[var(--border)]"><th className="py-2 font-medium">Seed</th><th className="py-2 font-medium">Mean</th><th className="py-2 font-medium">Minimum</th><th className="py-2 font-medium">Median</th><th className="py-2 font-medium">Maximum</th></tr></thead>
          <tbody>{seeds.map((seed) => { const row = rows.find((item) => item.seed === seed)!; return <tr key={seed} className="mono border-b border-[var(--border)] last:border-0"><td className="py-2">{seed}</td><td>{format.number(row.seed_mean_fidelity)}</td><td>{format.number(row.seed_min_fidelity)}</td><td>{format.number(row.seed_median_fidelity)}</td><td>{format.number(row.seed_max_fidelity)}</td></tr>; })}</tbody>
        </table>
      </div>
    </div>
  );
}

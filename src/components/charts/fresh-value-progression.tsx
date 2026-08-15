"use client";

import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SeedResult } from "@/lib/evidence/schemas";
import { format } from "@/lib/format";

export function FreshValueProgression({ rows }: { rows: SeedResult[] }) {
  const data = ["V0", "V1", "V2"].map((generation) => Object.fromEntries([
    ["generation", generation],
    ...rows.map((row) => [String(row.seed), row[`${generation.toLowerCase()}_fresh_approved_value` as keyof SeedResult]]),
  ]));
  const colors = ["#ff7a3d", "#65b2fb", "#4dd4ac", "#f8c35c", "#b7c6d8"];

  return (
    <div>
      <div className="mb-4 rounded-md border border-[rgb(248_195_92_/_0.55)] bg-[rgb(248_195_92_/_0.08)] p-3 text-sm font-medium text-[var(--warning)]">Matched-pool caveat: the action pool is fixed and held constant across generations.</div>
      <div className="h-[330px]" aria-hidden="true">
        <ResponsiveContainer>
          <LineChart accessibilityLayer={false} data={data} margin={{ top: 10, right: 16, bottom: 12, left: 10 }}>
            <CartesianGrid stroke="#20364f" vertical={false} />
            <XAxis dataKey="generation" tick={{ fill: "#b7c6d8", fontSize: 11 }} />
            <YAxis tick={{ fill: "#91a5ba", fontSize: 10 }} tickFormatter={(value) => `$${Math.round(Number(value) / 1000)}k`} />
            <Tooltip contentStyle={{ background: "#0b1a2c", border: "1px solid #2a425e", borderRadius: 8 }} formatter={(value, name) => [format.currency(Number(value)), `Seed ${name}`]} />
            <Legend wrapperStyle={{ fontSize: 10 }} />
            {rows.map((row, index) => <Line key={row.seed} name={String(row.seed)} type="linear" dataKey={String(row.seed)} stroke={colors[index]} strokeWidth={1.8} dot={{ r: 4 }} />)}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <table className="mt-4 w-full text-left text-xs">
        <caption className="sr-only">Fresh-attacker approved value by generation and seed</caption>
        <thead><tr className="border-b border-[var(--border)] text-[var(--text-muted)]"><th className="py-2">Seed</th><th>V0</th><th>V1</th><th>V2</th></tr></thead>
        <tbody>{rows.map((row) => <tr key={row.seed} className="mono border-b border-[var(--border)] last:border-0"><td className="py-2">{row.seed}</td><td>{format.currency(row.v0_fresh_approved_value)}</td><td>{format.currency(row.v1_fresh_approved_value)}</td><td>{format.currency(row.v2_fresh_approved_value)}</td></tr>)}</tbody>
      </table>
    </div>
  );
}

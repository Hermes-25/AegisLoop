"use client";

import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SeedResult } from "@/lib/evidence/schemas";
import { format } from "@/lib/format";

export function RewardComparison({ rows }: { rows: SeedResult[] }) {
  return (
    <div>
      <div className="h-[340px]" aria-hidden="true">
        <ResponsiveContainer>
          <LineChart accessibilityLayer={false} data={rows} margin={{ top: 12, right: 18, bottom: 20, left: 8 }}>
            <CartesianGrid stroke="#20364f" vertical={false} />
            <XAxis dataKey="seed" tick={{ fill: "#91a5ba", fontSize: 10 }} tickFormatter={(value) => String(value).slice(-2)} label={{ value: "Seed suffix", position: "bottom", fill: "#91a5ba", fontSize: 11 }} />
            <YAxis tick={{ fill: "#91a5ba", fontSize: 11 }} tickFormatter={(value) => format.number(value, 1)} />
            <Tooltip contentStyle={{ background: "#0b1a2c", border: "1px solid #2a425e", borderRadius: 8 }} labelFormatter={(label) => `Seed ${label}`} formatter={(value, name) => [format.number(Number(value)), String(name).replaceAll("_", " ")]} />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 12 }} />
            <Line name="Contextual bandit" type="linear" dataKey="contextual_bandit_reward" stroke="#ff7a3d" strokeWidth={2.5} dot={{ r: 5, fill: "#ff7a3d", stroke: "#081321", strokeWidth: 2 }} />
            <Line name="Random" type="linear" dataKey="random_reward" stroke="#65b2fb" strokeWidth={2} strokeDasharray="5 4" dot={{ r: 4, fill: "#65b2fb" }} />
            <Line name="Rule mutation" type="linear" dataKey="rule_mutation_reward" stroke="#b7c6d8" strokeWidth={2} strokeDasharray="2 4" dot={{ r: 4, fill: "#b7c6d8" }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <table className="mt-4 w-full text-left text-xs">
        <caption className="sr-only">Reward by strategy and seed</caption>
        <thead><tr className="border-b border-[var(--border)] text-[var(--text-muted)]"><th className="py-2">Seed</th><th>Bandit</th><th>Random</th><th>Rule mutation</th></tr></thead>
        <tbody>{rows.map((row) => <tr key={row.seed} className="mono border-b border-[var(--border)] last:border-0"><td className="py-2">{row.seed}</td><td>{format.number(row.contextual_bandit_reward)}</td><td>{format.number(row.random_reward)}</td><td>{format.number(row.rule_mutation_reward)}</td></tr>)}</tbody>
      </table>
    </div>
  );
}

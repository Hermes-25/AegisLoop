"use client";

import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SeedResult } from "@/lib/evidence/schemas";
import { format } from "@/lib/format";

export function NoveltyAblation({ rows }: { rows: SeedResult[] }) {
  return (
    <div className="h-[280px]" aria-hidden="true">
      <ResponsiveContainer>
        <LineChart accessibilityLayer={false} data={rows} margin={{ top: 10, right: 14, bottom: 12, left: 4 }}>
          <CartesianGrid stroke="#20364f" vertical={false} />
          <XAxis dataKey="seed" tick={{ fill: "#91a5ba", fontSize: 10 }} tickFormatter={(value) => String(value).slice(-2)} />
          <YAxis tick={{ fill: "#91a5ba", fontSize: 10 }} />
          <Tooltip contentStyle={{ background: "#0b1a2c", border: "1px solid #2a425e", borderRadius: 8 }} labelFormatter={(label) => `Seed ${label}`} formatter={(value) => format.number(Number(value))} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          <Line name="Novelty on" type="linear" dataKey="contextual_bandit_reward" stroke="#ff7a3d" strokeWidth={2} dot={{ r: 4 }} />
          <Line name="Novelty zeroed" type="linear" dataKey="contextual_bandit_no_novelty_reward" stroke="#f8c35c" strokeWidth={2} strokeDasharray="5 4" dot={{ r: 4 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

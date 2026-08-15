"use client";

import type { SeedResult } from "@/lib/evidence/schemas";
import { format } from "@/lib/format";

type Metric = "auc" | "recall" | "fpr";
const generations = ["V0", "V1", "V2"] as const;

export function DefenderProgression({ rows, metric }: { rows: SeedResult[]; metric: Metric }) {
  const values = generations.flatMap((generation) => rows.map((row) => row[`${generation.toLowerCase()}_held_out_${metric}` as keyof SeedResult] as number));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const padding = Math.max((max - min) * 0.25, metric === "fpr" ? 0.001 : 0.005);
  const lo = Math.max(0, min - padding);
  const hi = Math.min(1, max + padding);
  const x = (index: number) => 54 + index * 122;
  const y = (value: number) => 176 - ((value - lo) / Math.max(hi - lo, 1e-9)) * 136;
  const means = generations.map((generation) => rows.reduce((sum, row) => sum + (row[`${generation.toLowerCase()}_held_out_${metric}` as keyof SeedResult] as number), 0) / rows.length);
  return <div><svg viewBox="0 0 352 220" className="h-auto w-full" role="img" aria-label={`${metric.toUpperCase()} progression from V0 to V2 with all seed trajectories`}><line x1="42" y1="176" x2="314" y2="176" stroke="#2a425e" /><line x1="42" y1="40" x2="42" y2="176" stroke="#2a425e" /><text x="38" y="44" textAnchor="end" fill="#91a5ba" fontSize="9">{metric === "fpr" ? format.percent(hi, 1) : format.number(hi, 3)}</text><text x="38" y="179" textAnchor="end" fill="#91a5ba" fontSize="9">{metric === "fpr" ? format.percent(lo, 1) : format.number(lo, 3)}</text>{rows.map((row) => { const points=generations.map((generation,index)=>`${x(index)},${y(row[`${generation.toLowerCase()}_held_out_${metric}` as keyof SeedResult] as number)}`).join(" "); return <g key={row.seed}><polyline points={points} fill="none" stroke="#4c9be8" strokeOpacity="0.25" strokeWidth="1" />{generations.map((generation,index)=><circle key={generation} cx={x(index)} cy={y(row[`${generation.toLowerCase()}_held_out_${metric}` as keyof SeedResult] as number)} r="3" fill="#4c9be8" fillOpacity="0.55" />)}</g>; })}<polyline points={means.map((value,index)=>`${x(index)},${y(value)}`).join(" ")} fill="none" stroke="#4dd4ac" strokeWidth="2.5" />{means.map((value,index)=><circle key={generations[index]} cx={x(index)} cy={y(value)} r="5" fill="#4dd4ac" stroke="#081321" strokeWidth="2" />)}{generations.map((generation,index)=><text key={generation} x={x(index)} y="200" textAnchor="middle" fill="#b7c6d8" fontSize="11" fontWeight="600">{generation}</text>)}</svg><table className="w-full text-left text-xs"><caption className="sr-only">Mean {metric} by defender generation</caption><tbody>{generations.map((generation,index)=><tr key={generation} className="border-b border-[var(--border)] last:border-0"><th className="py-2 font-medium">{generation} mean</th><td className="mono text-right">{metric === "fpr" ? format.percent(means[index], 3) : metric === "recall" ? format.percent(means[index], 2) : format.number(means[index], 5)}</td></tr>)}</tbody></table></div>;
}

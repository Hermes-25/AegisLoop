"use client";

import { scaleLinear, scaleLog } from "d3";
import type { PrevalenceRow } from "@/lib/evidence/schemas";
import { format } from "@/lib/format";

const defenders = ["V0", "V1", "V2"] as const;
const colors = { V0: "#4c9be8", V1: "#ff7a3d", V2: "#4dd4ac" };

export function PrevalenceCollapse({ rows }: { rows: PrevalenceRow[] }) {
  const points = defenders.map((defender) => {
    const observed = rows.find((row) => row.defender === defender && row.scenario === "experiment_prevalence");
    const realistic = rows.find((row) => row.defender === defender && row.scenario === "deployment_exact_prevalence_reweighted_0.015pct");
    if (!observed || !realistic) throw new Error(`Missing prevalence endpoint for ${defender}`);
    return { defender, observed, realistic };
  });
  const width = 820, height = 430, left = 88, right = 32, top = 32, bottom = 78;
  const x = scaleLog().domain([0.0001, 0.15]).range([left, width - right]);
  const y = scaleLinear().domain([0, 1]).range([height - bottom, top]);
  const xTicks = [0.00015, 0.001, 0.01, 0.1];
  const yTicks = [0, 0.25, 0.5, 0.75, 1];
  return <div><svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full" role="img" aria-label="Precision collapse from experiment prevalence to realistic prevalence for V0, V1 and V2, seed 20260812"><rect x={left} y={top} width={width-left-right} height={height-top-bottom} fill="#0b1a2c" />{yTicks.map((tick)=><g key={tick}><line x1={left} x2={width-right} y1={y(tick)} y2={y(tick)} stroke="#20364f" /><text x={left-12} y={y(tick)+4} textAnchor="end" fill="#91a5ba" fontSize="11">{format.percent(tick,0)}</text></g>)}{xTicks.map((tick)=><g key={tick}><line x1={x(tick)} x2={x(tick)} y1={top} y2={height-bottom} stroke="#20364f" /><text x={x(tick)} y={height-bottom+25} textAnchor="middle" fill="#91a5ba" fontSize="10">{format.percent(tick,tick < 0.001 ? 3 : 1)}</text></g>)}<text x={(left+width-right)/2} y={height-20} textAnchor="middle" fill="#b7c6d8" fontSize="12">Fraud prevalence · logarithmic scale</text><text transform={`translate(22 ${(top+height-bottom)/2}) rotate(-90)`} textAnchor="middle" fill="#b7c6d8" fontSize="12">Precision</text>{points.map(({defender,observed,realistic},index)=>{ const color=colors[defender]; const offset=(index-1)*8; return <g key={defender}><line x1={x(realistic.prevalence)} y1={y(realistic.precision_mean)+offset} x2={x(observed.prevalence)} y2={y(observed.precision_mean)+offset} stroke={color} strokeWidth="2" strokeDasharray="6 5" /><circle cx={x(observed.prevalence)} cy={y(observed.precision_mean)+offset} r="7" fill={color} stroke="#081321" strokeWidth="2" /><path d={`M ${x(realistic.prevalence)-7} ${y(realistic.precision_mean)+offset+7} L ${x(realistic.prevalence)} ${y(realistic.precision_mean)+offset-7} L ${x(realistic.prevalence)+7} ${y(realistic.precision_mean)+offset+7} Z`} fill={color} stroke="#081321" strokeWidth="2" /><text x={x(observed.prevalence)+10} y={y(observed.precision_mean)+offset+4} fill={color} fontSize="11" fontWeight="600">{defender} {format.percent(observed.precision_mean,2)}</text><text x={x(realistic.prevalence)+10} y={y(realistic.precision_mean)+offset+4} fill={color} fontSize="11" fontWeight="600">{defender} {format.percent(realistic.precision_mean,2)}</text></g>;})}<rect x="318" y="185" width="184" height="30" rx="6" fill="#172b43" stroke="#f8c35c" /><text x="410" y="204" textAnchor="middle" fill="#f8c35c" fontSize="11" fontWeight="600">visual interpolation only</text></svg><div className="mt-4 flex flex-wrap justify-center gap-5 text-xs text-[var(--text-secondary)]">{defenders.map((defender)=><span key={defender} className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: colors[defender] }} />{defender}</span>)}<span>● experiment endpoint</span><span>▲ exact prevalence reweighting</span></div></div>;
}

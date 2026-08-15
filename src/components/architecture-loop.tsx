"use client";

import { motion } from "motion/react";

const nodes = [
  { label: "Identify", sub: "Threat atlas", x: 86, y: 80, tone: "blue" },
  { label: "Generate", sub: "Stateful twin", x: 316, y: 80, tone: "orange" },
  { label: "Adapt", sub: "Bandit policy", x: 316, y: 246, tone: "orange" },
  { label: "Defend", sub: "Hardened model", x: 86, y: 246, tone: "green" },
];

export function ArchitectureLoop() {
  return (
    <div className="panel-grid relative overflow-hidden rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-4" role="img" aria-label="AegisLoop closed loop: Identify, Generate, Adapt, Defend, then feed evidence back into Identify.">
      <svg viewBox="0 0 402 326" className="h-auto w-full" aria-hidden="true">
        <defs><marker id="arrow-orange" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#ff7a3d" /></marker><marker id="arrow-green" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#4dd4ac" /></marker></defs>
        <path d="M126 80 H276 Q316 80 316 120 V206" fill="none" stroke="#2a425e" strokeWidth="2" />
        <path d="M276 246 H126 Q86 246 86 206 V120" fill="none" stroke="#2a425e" strokeWidth="2" />
        <motion.path d="M126 80 H276 Q316 80 316 120 V206" fill="none" stroke="#ff7a3d" strokeWidth="3" markerEnd="url(#arrow-orange)" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.2, ease: "easeInOut" }} />
        <motion.path d="M276 246 H126 Q86 246 86 206 V120" fill="none" stroke="#4dd4ac" strokeWidth="3" markerEnd="url(#arrow-green)" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.2, delay: 1.1, ease: "easeInOut" }} />
        {nodes.map((node) => {
          const color = node.tone === "orange" ? "#ff7a3d" : node.tone === "green" ? "#4dd4ac" : "#4c9be8";
          return <g key={node.label}><circle cx={node.x} cy={node.y} r="39" fill="#0b1a2c" stroke={color} strokeWidth="2" /><circle cx={node.x} cy={node.y} r="31" fill="#12243a" /><text x={node.x} y={node.y - 2} textAnchor="middle" fill="#f4f8fc" fontSize="13" fontWeight="650">{node.label}</text><text x={node.x} y={node.y + 15} textAnchor="middle" fill="#91a5ba" fontSize="9">{node.sub}</text></g>;
        })}
        <text x="201" y="154" textAnchor="middle" fill="#f4f8fc" fontSize="16" fontWeight="650">Closed-loop</text>
        <text x="201" y="174" textAnchor="middle" fill="#91a5ba" fontSize="10">evidence becomes training data</text>
      </svg>
    </div>
  );
}

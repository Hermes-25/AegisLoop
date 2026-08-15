"use client";

import { useState } from "react";
import { ArrowRight, Bot, Layers3, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { AttackCard } from "@/lib/evidence/schemas";
import { format } from "@/lib/format";
import { cn } from "@/lib/utils";

export function AttackAtlasExplorer({ cards }: { cards: AttackCard[] }) {
  const [selectedFamily, setSelectedFamily] = useState(cards[0]?.family);
  const selected = cards.find((card) => card.family === selectedFamily) ?? cards[0];
  if (!selected) return null;

  return (
    <div className="grid gap-5 xl:grid-cols-[0.92fr_1.08fr]">
      <div className="grid gap-3 sm:grid-cols-2" role="list" aria-label="Attack archetypes">
        {cards.map((card) => {
          const active = card.family === selected.family;
          return <div key={card.family} role="listitem"><button aria-pressed={active} onClick={() => setSelectedFamily(card.family)} className={cn("h-full min-h-36 w-full rounded-[var(--radius)] border bg-[var(--surface)] p-4 text-left transition-colors", active ? "border-[var(--signal-orange)] shadow-[0_0_0_1px_var(--signal-orange)]" : "border-[var(--border)] hover:border-[var(--accent-blue)] hover:bg-[var(--surface-raised)]")}><div className="flex items-start justify-between gap-3"><Badge tone={active ? "orange" : "neutral"}>{card.rail}</Badge><span className="mono text-xs text-[var(--text-muted)]">{format.integer(card.variants.length)} variants</span></div><h2 className="mt-4 text-sm font-semibold leading-5">{card.title}</h2><p className="mt-2 text-xs text-[var(--text-muted)]">{card.channel}</p></button></div>;
        })}
      </div>

      <Card className="xl:sticky xl:top-24 xl:self-start">
        <CardContent className="p-6">
          <div className="flex flex-wrap items-center gap-2"><Badge tone="orange">Illustrative detail</Badge><Badge tone="blue">{selected.channel}</Badge></div>
          <h2 className="mt-5 text-2xl font-semibold tracking-tight">{selected.title}</h2>
          <p className="mt-3 text-base leading-7 text-[var(--text-secondary)]">{selected.objective}</p>
          <div className="mt-7 grid gap-5 sm:grid-cols-2">
            <div className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] p-4"><div className="flex items-center gap-2 text-[var(--accent-blue)]"><Bot className="h-4 w-4" /><span className="eyebrow !text-current">GenAI enabler</span></div><p className="mt-3 text-sm leading-6 text-[var(--text-secondary)]">{selected.genai_enabler}</p></div>
            <div className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] p-4"><div className="flex items-center gap-2 text-[var(--signal-orange)]"><Layers3 className="h-4 w-4" /><span className="eyebrow !text-current">Campaign envelope</span></div><p className="mono mt-3 text-sm">{format.currency(selected.amount_range[0])}–{format.currency(selected.amount_range[1])}</p><p className="mt-1 text-xs text-[var(--text-muted)]">{format.integer(selected.event_range[0])}–{format.integer(selected.event_range[1])} linked events</p></div>
          </div>
          <div className="mt-7"><p className="eyebrow">State sequence</p><ol className="mt-4 grid gap-2 sm:grid-cols-2">{selected.event_sequence.map((stage, index) => <li key={stage} className="flex items-center gap-3 rounded-md border border-[var(--border)] bg-[var(--chrome)] px-3 py-3"><span className="mono grid h-6 w-6 place-items-center rounded-full bg-[rgb(255_122_61_/_0.12)] text-xs text-[var(--signal-orange)]">{index + 1}</span><span className="text-sm">{stage.replaceAll("_", " ")}</span>{index < selected.event_sequence.length - 1 && <ArrowRight className="ml-auto h-3.5 w-3.5 text-[var(--text-muted)]" />}</li>)}</ol></div>
          <div className="mt-7"><p className="eyebrow">Scenario variants</p><div className="mt-3 flex flex-wrap gap-2">{selected.variants.map((variant) => <Badge key={variant}>{variant}</Badge>)}</div></div>
          <div className="mt-7"><p className="eyebrow">Mitigation hypotheses</p><ul className="mt-3 space-y-2">{selected.mitigations.map((mitigation) => <li key={mitigation} className="flex gap-2 text-sm text-[var(--text-secondary)]"><ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-[var(--defender)]" />{mitigation}</li>)}</ul></div>
        </CardContent>
      </Card>
    </div>
  );
}

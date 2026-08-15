"use client";

import { useState } from "react";
import { Clock3, Network, Smartphone, Store, UserRound } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { RepresentativeCampaign } from "@/lib/evidence/schemas";
import { format } from "@/lib/format";
import { cn } from "@/lib/utils";

export function CampaignTimeline({ campaign }: { campaign: RepresentativeCampaign }) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const selected = campaign.events[selectedIndex];
  const maxVelocity = Math.max(...campaign.events.map((event) => event.velocity_1h), 1);
  const maxShared = Math.max(...campaign.events.map((event) => event.graph_shared_entities), 1);

  return (
    <div>
      <div className="scrollbar-thin overflow-x-auto pb-4">
        <div className="relative flex min-w-[820px] items-start justify-between gap-2 pt-5 before:absolute before:left-8 before:right-8 before:top-10 before:h-px before:bg-[var(--border)]">
          {campaign.events.map((event, index) => <button key={event.event_id} onClick={() => setSelectedIndex(index)} aria-pressed={index === selectedIndex} aria-label={`Inspect event ${event.rollout_index}, ${event.sequence_stage.replaceAll("_", " ")}`} className="group relative z-10 w-20 text-center"><span className={cn("mono mx-auto grid h-10 w-10 place-items-center rounded-full border-2 bg-[var(--chrome)] text-xs transition-colors", index === selectedIndex ? "border-[var(--signal-orange)] text-[var(--signal-orange)]" : "border-[var(--border)] text-[var(--text-muted)] group-hover:border-[var(--accent-blue)]")}>{event.rollout_index}</span><span className="mt-3 block text-[0.65rem] leading-4 text-[var(--text-muted)]">{event.sequence_stage.replaceAll("_", " ")}</span></button>)}
        </div>
      </div>

      <div className="mt-3 grid gap-5 rounded-md border border-[var(--border)] bg-[var(--chrome)] p-5 lg:grid-cols-[0.9fr_1.1fr]">
        <div><div className="flex flex-wrap items-center gap-2"><Badge tone="orange">Event {format.integer(selected.rollout_index)}</Badge><Badge tone="blue">{selected.sequence_stage.replaceAll("_", " ")}</Badge></div><p className="mono mt-5 text-sm text-[var(--text)]">{format.timestamp(selected.timestamp)}</p><p className="mt-2 text-sm text-[var(--text-secondary)]">{selected.channel} · {selected.rail}</p><p className="mono mt-5 text-3xl font-semibold text-[var(--signal-orange)]">{format.currency(selected.amount)}</p></div>
        <div className="grid gap-3 sm:grid-cols-2"><Entity icon={UserRound} label="Customer" value={selected.customer_id} /><Entity icon={Smartphone} label="Device" value={selected.device_id} /><Entity icon={Store} label="Merchant" value={selected.merchant_id} /><Entity icon={Network} label="Beneficiary" value={selected.beneficiary_id} /></div>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-3">
        <Signal
          label="Velocity · 1 hour"
          value={selected.velocity_1h}
          maximum={maxVelocity}
          description="Payment attempts linked to this customer in the previous hour; a sudden spike can signal automated or coordinated activity."
          detail={`10-minute velocity: ${format.integer(selected.velocity_10m)}`}
          detailDescription="The same attempt count in the tighter ten-minute window, used to surface short bursts."
        />
        <Signal
          label="Shared graph entities"
          value={selected.graph_shared_entities}
          maximum={maxShared}
          description="Devices, merchants or beneficiaries this event shares with other campaign events, revealing hidden links between transactions."
          detail={`Graph degree: ${format.integer(selected.graph_degree)}`}
          detailDescription="The number of direct entity connections around this event in the simulated payment network."
        />
        <Signal
          label="Relationship reuse"
          value={selected.beneficiary_reuse_24h + selected.device_reuse_24h}
          maximum={Math.max(...campaign.events.map((event) => event.beneficiary_reuse_24h + event.device_reuse_24h), 1)}
          description="Combined recent reuse of the device and payee; repeated infrastructure can connect otherwise separate-looking payments."
          detail={`Device reuse: ${format.integer(selected.device_reuse_24h)} · Beneficiary reuse: ${format.integer(selected.beneficiary_reuse_24h)}`}
          detailDescription="Each value counts prior uses of that device or beneficiary during the previous 24 hours."
        />
      </div>
    </div>
  );
}

function Entity({ icon: Icon, label, value }: { icon: typeof Clock3; label: string; value: string }) {
  return <div className="rounded-md border border-[var(--border)] bg-[var(--surface)] p-3"><div className="flex items-center gap-2 text-xs text-[var(--text-muted)]"><Icon className="h-3.5 w-3.5" />{label}</div><p className="mono mt-2 text-xs text-[var(--text)]">{value}</p></div>;
}
function Signal({ label, value, maximum, description, detail, detailDescription }: { label: string; value: number; maximum: number; description: string; detail: string; detailDescription: string }) {
  const width = `${Math.max(3, (value / maximum) * 100)}%`;
  return <div className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] p-4"><div className="flex items-center justify-between gap-3"><p className="text-sm font-medium">{label}</p><span className="mono text-sm text-[var(--signal-orange)]">{format.integer(value)}</span></div><p className="mt-2 text-xs leading-5 text-[var(--text-secondary)]">{description}</p><div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[var(--chrome)]"><div className="h-full rounded-full bg-[var(--signal-orange)]" style={{ width }} /></div><div className="mt-3 border-t border-[var(--border)] pt-3"><p className="text-xs font-medium text-[var(--text)]">{detail}</p><p className="mt-1 text-xs leading-5 text-[var(--text-muted)]">{detailDescription}</p></div></div>;
}

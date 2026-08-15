import Link from "next/link";
import { ArrowRight, Database, ShieldCheck } from "lucide-react";

import { ArchitectureLoop } from "@/components/architecture-loop";
import { MetricCard } from "@/components/metric-card";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { summarizeV2CampaignDiagnostics } from "@/lib/evidence/diagnostics";
import { loadAggregate, loadAttackAtlas, loadPrevalenceMetrics, loadV2Diagnostics } from "@/lib/evidence/loader";
import { format } from "@/lib/format";

export default async function MissionBriefingPage() {
  const [aggregate, atlas, prevalence, diagnostics] = await Promise.all([
    loadAggregate(), loadAttackAtlas(), loadPrevalenceMetrics(), loadV2Diagnostics(),
  ]);
  const variantCount = atlas.reduce((sum, card) => sum + card.variants.length, 0);
  const diagnostic = summarizeV2CampaignDiagnostics(diagnostics);
  const v2Observed = prevalence.find((row) => row.defender === "V2" && row.scenario === "experiment_prevalence");
  const v2Realistic = prevalence.find((row) => row.defender === "V2" && row.scenario === "deployment_exact_prevalence_reweighted_0.015pct");
  if (!v2Observed || !v2Realistic) throw new Error("V2 prevalence endpoints are missing.");
  // `precision_mean` is the locked artifact column name. These aliases make its
  // seed-specific meaning explicit at the point where the UI consumes it.
  const v2ObservedSeedPrecision = v2Observed.precision_mean;
  const v2RealisticSeedPrecision = v2Realistic.precision_mean;

  return (
    <div className="space-y-10">
      <section className="grid items-center gap-8 xl:grid-cols-[1.12fr_0.88fr]">
        <div className="max-w-3xl">
          <div className="flex flex-wrap gap-2"><Badge tone="orange">Adversarial red team</Badge><Badge tone="blue">Synthetic-only</Badge><Badge tone="green"><ShieldCheck className="h-3 w-3" />Evidence locked</Badge></div>
          <p className="eyebrow mt-8">Mission briefing</p>
          <h1 className="mt-4 text-4xl font-semibold tracking-[-0.05em] sm:text-5xl lg:text-6xl">Find the fraud campaigns your current model has not learned to see.</h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-[var(--text-secondary)]">AegisLoop is an offline adversarial threat lab: a campaign-level attacker probes a frozen payment-fraud defender, valid evasions become hardening data, and every claimed improvement remains traceable to versioned evidence.</p>
          <div className="mt-8 flex flex-wrap gap-3"><Button asChild><Link href="/identify">Explore the attack atlas <ArrowRight className="h-4 w-4" /></Link></Button><Button asChild variant="secondary"><Link href="/evidence"><Database className="h-4 w-4" />Inspect evidence</Link></Button></div>
        </div>
        <ArchitectureLoop />
      </section>

      <section aria-labelledby="evidence-at-glance">
        <div className="mb-5 flex items-end justify-between gap-4"><div><p className="eyebrow">Evidence at a glance</p><h2 id="evidence-at-glance" className="mt-2 text-2xl font-semibold">What the full protocol establishes</h2></div><p className="hidden text-sm text-[var(--text-muted)] sm:block">No single seed promoted</p></div>
        <div className="grid gap-4 md:grid-cols-3">
          <MetricCard label="Attack breadth" value={`${format.integer(atlas.length)} / ${format.integer(variantCount)}`} detail="Equal-priority archetypes / total scenario variants in the machine-readable atlas." source="artifacts/precomputed/attack_atlas.json" field="array length / sum(variants.length)" tone="blue" />
          <MetricCard label="Adaptive attacker reward" value={`${format.number(aggregate.contextual_bandit_reward.mean)} [${format.number(aggregate.contextual_bandit_reward.ci95_low)}, ${format.number(aggregate.contextual_bandit_reward.ci95_high)}]`} detail="Seed-level mean with nonparametric bootstrap confidence interval under the full protocol." source="artifacts/full_multiseed/aggregate.json" field="contextual_bandit_reward.mean / ci95_low / ci95_high" tone="orange" />
          <MetricCard label="Matched-pool V2 diagnostic" value={`${format.integer(diagnostic.qualifyingCampaigns)} / ${format.integer(diagnostic.totalCampaigns)}`} detail={`${format.integer(diagnostic.validCampaigns)} fidelity-valid; ${format.integer(diagnostic.fullyDetectedCampaigns)} fully detected; ${format.integer(diagnostic.passingSeeds)}/${format.integer(diagnostic.totalSeeds)} seeds pass every campaign.`} source="artifacts/precomputed/v2_campaign_diagnostics.csv" field="count(valid && detection_rate == 1) / count(rows); all-pass seed count" tone="green" />
        </div>
      </section>

      <Card className="overflow-hidden border-[rgb(248_195_92_/_0.55)]">
        <CardContent className="grid gap-6 p-6 lg:grid-cols-[1fr_auto_1fr] lg:items-center">
          <div><p className="eyebrow !text-[var(--warning)]">Reality boundary · seed 20260812</p><p className="mt-3 text-xl font-semibold">Laboratory precision does not survive the production base rate unchanged.</p><p className="mt-2 text-sm leading-6 text-[var(--text-secondary)]">This caveat is part of the result, not a footnote.</p></div>
          <div className="hidden h-20 w-px bg-[var(--border)] lg:block" />
          <div className="flex items-center gap-5 sm:justify-end"><div><p className="text-xs uppercase tracking-wider text-[var(--text-muted)]">Experiment</p><p className="mono mt-1 text-2xl text-[var(--text)]">{format.percent(v2ObservedSeedPrecision)}</p></div><ArrowRight className="h-5 w-5 text-[var(--warning)]" /><div><p className="text-xs uppercase tracking-wider text-[var(--text-muted)]">Realistic prevalence</p><p className="mono mt-1 text-2xl text-[var(--warning)]">{format.percent(v2RealisticSeedPrecision)}</p></div></div>
        </CardContent>
      </Card>

      <Alert title="Defensible scope" tone="info">Against a matched, fixed action pool held constant across generations, the hardened defender (V2) detected every campaign across five seeds. This is not an unqualified claim that V2 stops fresh attackers or production fraud.</Alert>
    </div>
  );
}

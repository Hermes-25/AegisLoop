import { BrainCircuit, RefreshCw, ScanSearch, Target } from "lucide-react";

import { NoveltyAblation } from "@/components/charts/novelty-ablation";
import { RewardComparison } from "@/components/charts/reward-comparison";
import { MetricCard } from "@/components/metric-card";
import { PageHeader } from "@/components/page-header";
import { ProvenanceChip } from "@/components/provenance-chip";
import { RewardDecomposition } from "@/components/reward-decomposition";
import { Alert } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { loadAggregate, loadSeedResults, loadV2Diagnostics } from "@/lib/evidence/loader";
import { format } from "@/lib/format";

export const metadata = { title: "Adapt · Red-Team Arena" };

const banditSteps = [
  [ScanSearch, "Read the defender", "Recent detection, fidelity and family coverage form the context."],
  [Target, "Choose a campaign", "The policy balances promising actions with uncertain ones."],
  [BrainCircuit, "Observe immediate reward", "A valid campaign is scored after one defender response."],
  [RefreshCw, "Update the policy", "The next selection uses what the arena just learned."],
] as const;

export default async function AdaptPage() {
  const [aggregate, seeds, diagnostics] = await Promise.all([
    loadAggregate(),
    loadSeedResults(),
    loadV2Diagnostics(),
  ]);
  const noveltyTest = aggregate.significance_tests.novelty_on_vs_off;

  return (
    <div>
      <PageHeader
        eyebrow="Adapt · Red-team arena"
        title="The attacker learns which valid campaigns expose the current defender."
        conclusion="Under an equal full-campaign budget, LinUCB outperformed random and rule-mutation search across every fixed seed; the novelty bonus itself produced no measurable improvement."
      >
        <ProvenanceChip source="artifacts/full_multiseed/aggregate.json" field="strategy reward summaries and significance_tests" />
      </PageHeader>

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Contextual bandit" value={format.number(aggregate.contextual_bandit_reward.mean)} detail={`95% CI ${format.number(aggregate.contextual_bandit_reward.ci95_low)} to ${format.number(aggregate.contextual_bandit_reward.ci95_high)}`} source="artifacts/full_multiseed/aggregate.json" field="contextual_bandit_reward" tone="orange" />
        <MetricCard label="Random search" value={format.number(aggregate.random_reward.mean)} detail={`95% CI ${format.number(aggregate.random_reward.ci95_low)} to ${format.number(aggregate.random_reward.ci95_high)}`} source="artifacts/full_multiseed/aggregate.json" field="random_reward" tone="blue" />
        <MetricCard label="Rule mutation" value={format.number(aggregate.rule_mutation_reward.mean)} detail={`95% CI ${format.number(aggregate.rule_mutation_reward.ci95_low)} to ${format.number(aggregate.rule_mutation_reward.ci95_high)}`} source="artifacts/full_multiseed/aggregate.json" field="rule_mutation_reward" tone="amber" />
      </div>

      <Card className="mt-6">
        <CardHeader>
          <div><CardTitle>Every seed remains visible</CardTitle><CardDescription>Connected points aid seed tracking; they do not imply temporal continuity.</CardDescription></div>
          <ProvenanceChip source="artifacts/full_multiseed/seed_results.csv" field="*_reward by seed" />
        </CardHeader>
        <CardContent><RewardComparison rows={seeds} /></CardContent>
      </Card>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader><div><CardTitle>LinUCB, in plain language</CardTitle><CardDescription>A lightweight contextual bandit—not a long-horizon MDP.</CardDescription></div></CardHeader>
          <CardContent>
            <ol className="space-y-4">
              {banditSteps.map(([Icon, title, body], index) => (
                <li key={title} className="flex gap-4">
                  <span className="mono grid h-8 w-8 shrink-0 place-items-center rounded-full border border-[var(--border)] bg-[var(--chrome)] text-xs text-[var(--signal-orange)]">{index + 1}</span>
                  <div><div className="flex items-center gap-2"><Icon className="h-4 w-4 text-[var(--accent-blue)]" /><p className="font-semibold">{title}</p></div><p className="mt-1 text-sm leading-6 text-[var(--text-secondary)]">{body}</p></div>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <CardTitle>Reward terms · V2 fresh-attacker diagnostic only</CardTitle>
              <CardDescription>Matched-pool hardening-stage campaigns—not the equal-budget strategy comparison above.</CardDescription>
            </div>
            <ProvenanceChip source="artifacts/precomputed/v2_campaign_diagnostics.csv" field="strategy == fresh_bandit_v2; value_term + evasion_term + detection_cost_term + resource_cost_term + novelty_term; multiplied by fidelity" />
          </CardHeader>
          <CardContent>
            <Alert title="Different evaluation stage" tone="info" className="mb-5">These terms explain the V2 matched-pool fresh-attacker diagnostic. They are not a term-by-term attribution of the headline bandit-versus-random-versus-rule-mutation comparison.</Alert>
            <RewardDecomposition rows={diagnostics} />
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6 border-[rgb(248_195_92_/_0.55)]">
        <CardHeader>
          <div><CardTitle>Null result · novelty bonus did not move performance</CardTitle><CardDescription>This receives the same visual weight as the positive baseline comparison.</CardDescription></div>
          <ProvenanceChip source="artifacts/full_multiseed/aggregate.json and artifacts/full_multiseed/seed_results.csv" field="contextual_bandit_no_novelty_reward, novelty_ablation_reward_delta, significance_tests.novelty_on_vs_off" />
        </CardHeader>
        <CardContent className="grid gap-6 lg:grid-cols-[1fr_300px]">
          <NoveltyAblation rows={seeds} />
          <div className="rounded-md border border-[var(--border)] bg-[var(--chrome)] p-5">
            <p className="eyebrow !text-[var(--warning)]">Two-sided paired test</p>
            <p className="mono mt-5 text-3xl text-[var(--warning)]">p = {format.number(Number(noveltyTest.p_value_two_sided))}</p>
            <p className="mono mt-4 text-sm">Δ = {format.number(aggregate.novelty_ablation_reward_delta.mean)}</p>
            <p className="mt-4 text-sm leading-6 text-[var(--text-secondary)]">The evidence does not support keeping novelty as a performance claim. The term remains logged for auditability.</p>
          </div>
        </CardContent>
      </Card>

      <Alert className="mt-6" title="Interpretation">The paired one-sided Wilcoxon result is p = {format.number(Number(aggregate.significance_tests.bandit_vs_random.p_value_one_sided))} versus random and p = {format.number(Number(aggregate.significance_tests.bandit_vs_rule.p_value_one_sided))} versus rule mutation. Five seed pairs support a directional comparison, not a production guarantee.</Alert>
    </div>
  );
}

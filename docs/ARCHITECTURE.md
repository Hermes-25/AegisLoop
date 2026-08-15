# Architecture and technical validity

## End-to-end pipeline

1. **Threat compiler:** eight safe attack archetypes and 32 variants are exported as a scenario
   DSL. GenAI helps structure research hypotheses at design time; no free-form attack endpoint is
   part of the product.
2. **Hand-coded payment digital twin:** a deterministic, PaySim-style agent simulation creates
   customers, devices, merchants and beneficiaries, then rolls out stateful 5–20-event campaigns.
3. **Fidelity firewall:** schema, range, chronology, behavioural and entity-reuse checks reject a
   campaign before it can earn reward.
4. **Contextual-bandit red team:** a shared LinUCB policy chooses complete campaign parameters from
   context derived from recent black-box defender outcomes. The frozen defender returns immediate
   campaign reward, making this a contextual bandit rather than a long-horizon MDP.
5. **Blue-team defender:** supervised gradient boosting, unsupervised isolation scoring and
   explicit relationship/intent risk produce a score and approve/step-up/hold/decline outcome.
6. **Generation boundary:** only valid evasions with positive approved value are archived. A new
   defender is trained, recalibrated on the unchanged legitimate validation split, frozen, and
   attacked again. Phase 1 implements V0→V1→V2.

## Simulator design choice and the Sajja paper

AegisLoop is **not CTGAN, TVAE, GaussianCopula, TabularARGN, or another learned row-independent
generator**. It is a hand-coded, stateful, entity-linked agent simulation. Campaign construction
selects shared customer/device/merchant/beneficiary entities once and then evolves timestamps,
reuse counts, velocity and graph aggregates across ordered events.

This choice is aligned with Bhavana Sajja, *Synthetic Tabular Generators Fail to Preserve
Behavioral Fraud Patterns: A Benchmark on Temporal, Velocity, and Multi-Account Signals*,
arXiv:2604.13125 (2026). Its Proposition 1 shows that row-independent generators cannot preserve
multi-account graph motifs, and Proposition 2 addresses inter-event-time autocorrelation. The
paper is used here to justify avoiding row-independent learned generation—not as proof that
AegisLoop matches real fraud. Because competition rules permit synthetic/authorized data only and
AegisLoop has no real reference corpus, its fidelity evidence is structural validity plus internal
diagnostics, not a TSTR or real-data fidelity claim.

Simulator and defender are separate code paths. The simulator writes synthetic event features;
the defender independently preprocesses and scores them. The fidelity gate does inspect some of
the same observable campaign fields because those are the invariants it validates, but it does
not use defender probabilities or thresholds and cannot approve a reward on the defender’s behalf.

## Reward normalization and decomposition

For a valid campaign:

`R = F × (V/500 + 2.5(1−D) − 0.16D − 2.5N/1000 + 0.20I_novel)`

where `F∈[0,1]` is fidelity, `V` is approved value, `D∈[0,1]` is event detection rate, `N=12`
events under the benchmark, and `I_novel` is one only for a first successful discretized pattern.
The value divisor makes hundreds of approved-value units comparable with the bounded evasion term;
detection and resource terms are explicit costs. An invalid campaign receives −1 and zero component
terms. The campaign CSV logs `value_term`, `evasion_term`, `detection_cost_term`,
`resource_cost_term`, `novelty_term`, `validity_term`, `pre_fidelity_reward`, `fidelity`, and final
`reward`.

The full five-seed ablation finds novelty-on minus novelty-off mean reward −0.017 (95% CI
[−0.137, 0.121], two-sided paired Wilcoxon p=0.625). Novelty is therefore **not** part of the
performance claim; it remains configurable for research traceability.

## Data roles and generation integrity

- Four **known** families provide campaign-disjoint supervised train/validation/test examples.
- Two **adaptive** families are absent from initial supervised data but are available to the
  red-team policy. Successful evasions can enter V1/V2 training.
- Two **final held-out** families are generated separately and excluded from all defender training,
  validation, red-team search and hardening. They test cross-family generalization for V0/V1/V2.
- Legitimate traffic is temporal: 0%–60% train, 60%–80% calibration validation, 80%–100% test.

## Deployment boundary

AegisLoop is an offline threat laboratory, not a live payment attacker. The red-team policy never
connects to payment rails. Production mapping would require governed feature pipelines, outcome
labels, drift monitoring, model-risk approval and champion/challenger rollout; none is claimed to
exist in this prototype.

## Final web command center

The judge-facing prototype is a Next.js App Router application with nine sections aligned to the
solution paper: Mission Briefing, Identify, Generate, Adapt, Defend, Reality Check, Evidence &
Governance, Live Benchmark and Methodology. Server Components load versioned evidence through a
single Zod-validated manifest; browser components receive only validated serializable records.
`/api/health` fails closed if any approved artifact is missing or malformed, and
`/api/evidence/[artifact]` exposes the same validated payload used by each chart.

The approved evidence manifest contains seven files: `aggregate.json`, `seed_results.csv`,
`calibration_audit.json`, `prevalence_metrics.csv`, `v2_campaign_diagnostics.csv`,
`attack_atlas.json` and `representative_campaign.json`. The representative rollout is generated
reproducibly by `scripts/make_representative_campaign.py`; it is a real deterministic simulator
output with linked entities, ordered timestamps and evolving velocity/relationship features.

The default orange control uses `#0A1B30` text on `#FF7A3D`; automated contrast and end-to-end
WCAG 2 A/AA scans guard the rendered interface. The hosted quick-run function has independent
client and server timeouts and returns explicit failed/timed-out states without affecting the
archived evidence or the rest of the command center.

## Primary references

- Sajja (2026), arXiv:2604.13125: https://arxiv.org/abs/2604.13125
- Vangara & Egg (2024), arXiv:2412.00569: https://arxiv.org/abs/2412.00569
- FRAUD-RLA (2025), arXiv:2502.02290: https://arxiv.org/abs/2502.02290

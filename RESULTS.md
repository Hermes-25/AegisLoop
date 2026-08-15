# Phase 1 verified results

These are the post-audit results. The headline evidence is the fixed five-seed **full** protocol
in `artifacts/full_multiseed/`, not the former single-seed run. All intervals are nonparametric
bootstrap 95% confidence intervals for the seed-level mean (20,000 draws); `±` is sample SD.

## Full-protocol red-team benchmark (five fixed seeds)

Each strategy receives 72 campaign evaluations of 12 linked events against the same frozen V0,
fidelity gate and search-family set. Seeds are 20260812–20260816.

| Strategy | Mean reward ± SD | 95% CI | Wins vs bandit |
|---|---:|---:|---:|
| Contextual bandit | **0.807 ± 0.457** | **[0.519, 1.212]** | — |
| Rule mutation | 0.503 ± 0.602 | [0.167, 1.047] | 0/5 |
| Random search | 0.126 ± 0.139 | [0.020, 0.235] | 0/5 |

The contextual bandit beats random on all five paired seeds (mean paired difference 0.681,
95% CI [0.489, 0.984], one-sided paired Wilcoxon signed-rank **p=0.03125**) and beats rule
mutation on all five (mean paired difference 0.304, 95% CI [0.125, 0.483], **p=0.03125**).
With n=5, the smallest attainable exact one-sided p-value when every non-zero pair has the same
sign is 0.03125; the evidence is positive but still small-sample.

The former single-seed reward of 1.642 is withdrawn. After the reward-code reconciliation and
leakage repair, the corresponding fixed seed produces 1.579; it lies inside the new full-protocol
distribution and is not used as the headline.

## Reward decomposition and novelty ablation

For a fidelity-valid campaign:

`reward = fidelity × (approved_value / 500 + 2.5 × evasion_rate − 0.16 × detection_rate − 2.5 × event_count / 1000 + 0.20 × first_novel_success)`

Invalid campaigns receive −1 and do not receive component rewards. Every component is logged in
`attack_strategy_runs.csv`. On seed 20260812, the contextual-bandit mean pre-fidelity components
are: value +1.120, evasion +0.616, detection −0.121, resource −0.030 and novelty +0.008.

| Full five-seed ablation | Mean reward ± SD | 95% CI |
|---|---:|---:|
| Novelty on | 0.807 ± 0.457 | [0.519, 1.212] |
| Novelty zeroed | 0.824 ± 0.349 | [0.574, 1.105] |
| Paired on − off | **−0.017 ± 0.159** | **[−0.137, 0.121]** |

The novelty term does **not** improve the result (two-sided paired Wilcoxon p=0.625). It is kept
only as an experimental field for traceability and is not claimed as a performance driver. The
approved-value and evasion terms carry the objective.

## Leakage-free defender generations

The threshold for each defender is selected independently on 5,600 legitimate rows from the
temporal validation window (60%–80%) at a 1% target FPR. The held-out evaluation uses the later
5,600 legitimate rows (80%–100%) plus two separately generated attack families. Validation/test
event-ID overlap is zero. Test rows are never used to choose or tighten a threshold.

Two families are exposed only through adaptive red-team search; two different families remain
unseen through all hardening and form the final generalization test.

| Held-out-family metric | V0 mean ± SD | V1 mean ± SD | V2 mean ± SD |
|---|---:|---:|---:|
| ROC-AUC | 0.9806 ± 0.0062 | 0.9938 ± 0.0049 | **0.99993 ± 0.00010** |
| Precision at experiment prevalence | 90.68% ± 1.92% | 90.73% ± 1.06% | **91.28% ± 1.72%** |
| Recall | 86.59% ± 3.05% | 96.06% ± 3.15% | **99.90% ± 0.15%** |
| Realized legitimate test FPR | 0.911% ± 0.163% | 1.007% ± 0.111% | 0.982% ± 0.200% |

V1 AUC exceeds V0 on 5/5 seeds (mean +0.0132; one-sided paired Wilcoxon p=0.03125). FPRs are
similar but deliberately **not forced to be identical**: each is the natural test realization of
a validation-calibrated 1% operating point.

## Fresh adaptive attacker and the V1→V2 stability check

The same newly sampled action space and deterministic attack random stream are used against each
frozen generation, so differences come from the defender and the attacker’s response to it.

| Fresh-attacker outcome | V0 | V1 | V2 |
|---|---:|---:|---:|
| Mean reward ± SD | 1.294 ± 0.666 | −0.043 ± 0.134 | **−0.175 ± 0.001** |
| Approved value, mean ± SD | 31,179 ± 18,851 | 1,673 ± 1,676 | **0 ± 0** |
| Approved-value reduction | — | **92.1% ± 8.2% vs V0** | **100% vs V1** |

V1 lowers fresh-attacker reward on 5/5 seeds (mean paired reduction 1.338, 95% CI
[0.880, 1.932], one-sided paired Wilcoxon p=0.03125). V2 is directionally harder than V1 on
four seeds with one tie (mean reward reduction 0.132, p=0.0625). Thus this experiment finds **no
oscillation through V2**, but n=5 is insufficient to claim oscillation risk has been eliminated.
The exact zero approved value at V2 is a synthetic-lab result, not a production guarantee.

The campaign-level audit is published as
`artifacts/precomputed/v2_campaign_diagnostics.csv` (artifact version 1.0). It confirms 72/72
fidelity-valid campaigns and 72/72 fully detected campaigns per seed, with 31-37 unique actions
selected. Therefore, the precise supported claim is: **against a matched, fixed action pool held
constant across generations, the hardened defender (V2) detected every campaign across five
seeds**. This is not a claim about independently resampled action spaces or live attackers.

## Prevalence stress test

The full synthetic corpus has 3,115 attack and 28,000 legitimate events (10.01% attack); the
held-out test slice is 9.39% attack. That density is for efficient controlled evaluation and is
not production prevalence. The ECB/EBA reported card fraud at 0.015% of transaction count in
H1 2023, so AegisLoop also reweights the same held-out scores to a 0.015% deployment scenario.

| Seed 20260812 held-out metric | V0 experiment 9.39% | V0 reweighted 0.015% | V1 experiment 9.39% | V1 reweighted 0.015% | V2 experiment 9.39% | V2 reweighted 0.015% |
|---|---:|---:|---:|---:|---:|---:|
| ROC-AUC | 0.9886 | 0.9886 | 0.9961 | 0.9961 | 0.9998 | 0.9998 |
| Precision | 91.89% | **1.61%** | 90.40% | **1.35%** | 90.17% | **1.31%** |
| Legitimate FPR | 0.821% | 0.821% | 1.071% | 1.071% | 1.125% | 1.125% |

AUC and FPR are prevalence-invariant for fixed scores/thresholds; precision is not. The sharp
precision collapse is the honest result and demonstrates why the experiment-prevalence precision
must not be presented as a production estimate. A 400-repeat literal downsampling diagnostic is
also in `prevalence_metrics.csv`; at this test-set size it contains only one fraud row per repeat,
so the exact prevalence-reweighted estimate is the more stable descriptive statistic.

## What changed from the former results

- Full and quick protocols are now named and stored separately. The old quick study used 9,000
  legitimate events, 14 campaigns/family, 36 bandit updates and 10 action variants/family; full
  uses 28,000, 42, 72 and 16 respectively. Their distributions were never directly comparable.
- The test-set threshold adjustment that made V0 and V1 both read 0.82% FPR was removed.
- Hardening now has two real transitions (V0→V1→V2), and final held-out families never enter
  attacker search or defender training.
- The reward’s configured detection-cost coefficient is now the implemented coefficient, every
  reward term is logged, and novelty is reported as an inert ablation rather than a claimed driver.

## Verification

- `10` focused tests pass: attack DSL bounds/serialization, simulator determinism and fidelity,
  defender scoring/actions/calibration metadata, red-team execution/reward reconciliation, and
  prototype/launcher resilience guards.
- Ruff passes on `src/`, `experiments/`, `tests/` and `app.py`.
- Detailed seed rows, confidence intervals and test statistics are in
  `artifacts/full_multiseed/seed_results.csv` and `aggregate.json`.

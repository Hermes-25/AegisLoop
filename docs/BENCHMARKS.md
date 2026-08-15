# Benchmark and evidence contract

## Full versus quick protocol (F-001)

The former results placed one full seed beside a five-seed quick study without clearly stating
that they were different experiments. That was misleading even though both code paths were
intentional. The protocols differ as follows:

| Dimension | Quick judge smoke test | Full evidence protocol |
|---|---:|---:|
| Legitimate events | 9,000 | 28,000 |
| Campaigns generated per reference family | 14 | 42 |
| Campaign evaluations per strategy | 36 | 72 |
| Events per campaign evaluation | 12 | 12 |
| Action variants per search family | 10 | 16 |
| Fresh-action variants per family | 14 | 20 |
| Hardening transitions | 2 | 2 |
| Intended use | UI/liveness check | Quantitative evidence |

Larger data changes the fitted defender and threshold; a larger action space and doubled online
budget change the bandit trajectory. Quick and full reward/AUC distributions are therefore not
estimates of the same protocol. Artifacts are now stored as `quick_multiseed/` and
`full_multiseed/`; only full is used for headline claims.

The corrected full protocol is run on the fixed seeds 20260812–20260816. Seed 20260812’s bandit
reward is 1.579, inside the full five-seed range [0.463, 1.579]. The old 1.642 reflected the former
hard-coded reward coefficient and broader, non-independent held-out design; it is withdrawn.

## Threshold calibration audit (F-002)

For every seed:

| Split | Legitimate rows (full) | Selection | Role |
|---|---:|---|---|
| Train | 16,800 | chronological 0%–60% | Fit preprocessor, classifier and anomaly model |
| Validation | 5,600 | chronological 60%–80% | Select each defender’s 99th-percentile effective-score threshold |
| Test | 5,600 | chronological 80%–100% | Report FPR, recall, precision and AUC only |

V0, V1 and V2 share the same validation rows but compute separate thresholds because their scores
differ. The code asserts zero event-ID overlap between validation and test and zero campaign-ID
overlap across known-family train/validation/test partitions. `calibration_audit.json` records the
rows, thresholds, validation FPR and the explicit flag `test_rows_used_for_threshold_selection:
false`.

The former conditional block that tightened V1 with `legit_test` when its FPR exceeded V0 has been
deleted. The corrected test FPRs are allowed to differ; their five-seed means are V0 0.911%, V1
1.007% and V2 0.982% after validation calibration to 1%.

## Equal-budget comparisons and statistics

Random, rule mutation and contextual bandit receive the same frozen V0, search families, action
pool size, validity gate, 72×12 event budget and seed schedule. The test is paired at the seed
level. One-sided Wilcoxon signed-rank is specified in advance for the directional claim that the
bandit reward exceeds each baseline. Bootstrap 95% CIs use 20,000 resamples of seed-level values.

This n=5 study is small. Exact p=0.03125 occurs only because all five paired differences have the
predicted sign; uncertainty intervals and raw seed rows are published to prevent the p-value from
standing alone.

## Multi-generation stability

Vangara and Egg, *Contextual Bandits in Payment Processing: Non-uniform Exploration and Supervised
Learning at Adyen* (arXiv:2412.00569), describe later-generation degradation and a possible
oscillation effect under reward-distribution shift and class imbalance. AegisLoop therefore runs
two hardening transitions and attacks V0, V1 and V2 with the same fresh action space and random
stream.

V1 lowers fresh-attacker reward on all five seeds (p=0.03125). V2 is lower on four seeds and ties
on one (p=0.0625). There is no observed degradation through V2, but this is not evidence that
oscillation is impossible; more generations and more seeds are required.

The versioned campaign-level diagnostic for V2 is
`artifacts/precomputed/v2_campaign_diagnostics.csv` (artifact version 1.0). It contains all 360
V2 campaign evaluations: 72 per seed across five seeds. Each seed records 72/72 fidelity-valid
campaigns, 72/72 campaigns with every event detected, 864 generated events, zero approved value,
and 31-37 unique actions. This artifact supports only the following bounded claim: **against a
matched, fixed action pool held constant across generations, the hardened defender (V2) detected
every campaign across five seeds**. It does not establish performance against independently
resampled or live attackers.

## Prevalence protocol

The controlled held-out slice has 580 attack and 5,600 legitimate events for seed 20260812
(9.39% attack). For a realistic stress scenario, scores are importance-weighted to 0.015% attack
prevalence, matching the ECB/EBA H1 2023 reported share of fraudulent card payments by transaction
count. AUC and FPR stay fixed at a fixed score/threshold; precision is recomputed using class
weights. Literal downsampling is also repeated 400 times, but yields one positive per repeat and
is reported as a high-variance sensitivity check rather than the primary estimate.

Source: ECB/EBA, *Joint report on payment fraud*, H1 2023 card-fraud volume rate 0.015%:
https://www.ecb.europa.eu/press/pr/date/2024/html/ecb.pr240801~f21cc4a009.en.html

## Reproduction

```powershell
.venv\Scripts\python -m pytest
.venv\Scripts\python -m ruff check src experiments tests app.py
.venv\Scripts\python experiments\run_multiseed.py --seeds 20260812,20260813,20260814,20260815,20260816
```

The last command defaults to the full protocol and writes `artifacts/full_multiseed/`.
Add `--quick` only for a smoke test; it writes `artifacts/quick_multiseed/` by default.

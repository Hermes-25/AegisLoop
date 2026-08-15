# Phase 1 red-team remediation changelog

## F-001 — protocol inconsistency (P0)

- Confirmed that quick and full were materially different workloads; documented every difference
  in `docs/BENCHMARKS.md` and separated artifact directories.
- Withdrew the old single-seed 1.642/0.969→0.996/97.9% headline bundle.
- Ran the corrected full budget over five fixed seeds and published raw rows, mean ± SD, bootstrap
  95% CIs and paired Wilcoxon tests.
- New headline: bandit reward 0.807 ± 0.457 versus random 0.126 ± 0.139 and rule 0.503 ± 0.602;
  the bandit wins 5/5 against each, p=0.03125 one-sided.

## F-002 — threshold-on-test leakage (P0)

- Finding confirmed. Deleted the V1 test-row threshold-tightening block.
- V0/V1/V2 thresholds now come only from the legitimate temporal validation split.
- Added overlap assertions, calibration metadata, `calibration_audit.json`, and a calibration test.
- Corrected five-seed test FPR means are 0.911%, 1.007% and 0.982%; they are no longer forced equal.

## F-005 — reward normalization and novelty (P1)

- Made all coefficients configurable and corrected the code/config mismatch for detection cost.
- Added per-campaign decomposition fields and an exact-reconciliation test.
- Added a paired novelty-zero ablation across the full five seeds.
- Negative result: novelty-on minus off = −0.017 ± 0.159, p=0.625. Novelty is no longer claimed
  as a driver.

## Simulator fidelity question

- Verified and documented that AegisLoop is a hand-coded, stateful, entity-linked agent simulator,
  not a learned row-independent generator.
- Corrected the use of Sajja (2026): it justifies this design choice but does not prove real-data
  fidelity for AegisLoop.

## Class prevalence sanity check

- Added `prevalence_metrics.csv` with current-prevalence, literal downsampling and exact
  prevalence-reweighted evaluation at 0.015%.
- Published the precision collapse at deployment prevalence instead of implying that 90%+
  experiment-prevalence precision transfers to production.

## V1→V2 stability / Adyen warning

- Implemented a second genuine hardening transition.
- V2 does not degrade in these five seeds; fresh reward is lower on four with one tie (p=0.0625).
  This is reported as directional evidence, not proof of stability.
- Introduced three attack roles so final held-out families remain outside all search and training.

## F-003 — quick-benchmark timeout

- Added `TimeoutExpired` and process-start error handling to the Streamlit benchmark control.

## F-006 — evidence loading

- Added missing/malformed-file handling and required-key validation. The app now shows a readable
  recovery instruction and stops safely rather than rendering a traceback.

## F-007 — cross-platform launch

- Added `run_demo.sh` with Python 3.11 validation, virtual-environment setup and Streamlit launch.

## Verification

- 10 focused tests pass.
- Ruff passes across source, experiments, tests and the app.
- Full five-seed artifacts are in `artifacts/full_multiseed/`; the corrected seed-20260812 detailed
  artifact set is in `artifacts/precomputed/`.

Phase 2 files—README narrative, dashboard metric claims and slide deck—were intentionally not
updated. They remain pending user sign-off on these Phase 1 numbers.


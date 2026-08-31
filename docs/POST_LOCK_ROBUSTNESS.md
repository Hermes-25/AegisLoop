# Post-Lock V2 Robustness Audit

**Audit date:** 28 August 2026  
**Code revision tested:** `c37586b15d2205c9495881778827d39c3444e7bd`  
**Artifact version:** 1.0

## Purpose

The primary paper reports a deliberately bounded V2 result against a matched, fixed action pool. This supplementary audit asks whether that result survives independently regenerated bounded action pools and stronger search pressure. It does not replace or retrospectively alter the locked paper, application, or original seven-artifact evidence set.

## Reproducible protocol

The script [`experiments/run_post_lock_robustness.py`](../experiments/run_post_lock_robustness.py) rebuilds the submitted V0 -> V1 -> V2 training path for defender seeds `20260812` through `20260816`, then runs two separate conditions:

1. **Independent-pool condition.** Three newly generated action pools and independent arena random streams per defender seed. Each pool contains 120 candidates (20 variants across each of six configured search families), and each run retains the original 72-campaign exploration budget. This produces 15 runs and 1,080 campaigns.
2. **Double-search-pressure condition.** One newly generated pool per defender seed with 240 candidates (40 variants per family) and a 144-campaign budget. This produces five runs and 720 campaigns.

The action-pool seed and arena seed are distinct for every run and recorded in [`run_summary.csv`](../artifacts/post_lock_robustness/run_summary.csv). Campaigns inside a LinUCB run are sequentially dependent; campaign counts must therefore not be presented as independent Bernoulli trials.

Run from the repository root:

```bash
python experiments/run_post_lock_robustness.py
python experiments/diagnose_post_lock_escape.py
```

The full protocol retrains five V2 defenders and is intentionally more expensive than the illustrative web benchmark.

## Results

| Condition | Runs | Campaigns valid | Campaigns fully detected | Approved synthetic value |
|---|---:|---:|---:|---:|
| Independently resampled bounded pools | 15 | 1,080 / 1,080 | 1,080 / 1,080 | 0.000000 |
| Doubled candidate density and search budget | 5 | 720 / 720 | 719 / 720 | 8.936489 |

Under doubled search pressure, the only non-fully-detected campaign occurred for defender seed `20260813` in the `adaptive_card_testing` family. Eleven of its 12 events were detected. The approved event was worth 8.936489 synthetic units; its score of 0.176282 was 0.003095 below its event-specific operating threshold of 0.179378. The forensic record is versioned in [`stress_escape_diagnostic.json`](../artifacts/post_lock_robustness/stress_escape_diagnostic.json).

## Interpretation boundary

The matched-pool result remained intact across the independently regenerated bounded pools at the original exploration budget. The stronger search condition also establishes a non-zero boundary rather than a perfection claim. These remain offline synthetic tests inside the configured action distribution; they do not demonstrate universal protection against independently designed, open-ended future attackers or live payment traffic.

## Versioned evidence

| File | Scope |
|---|---|
| [`aggregate.json`](../artifacts/post_lock_robustness/aggregate.json) | Version, tested revision, protocol identity and condition-level totals |
| [`run_summary.csv`](../artifacts/post_lock_robustness/run_summary.csv) | All 20 seed/condition/replicate runs, including pool and arena seeds |
| [`campaign_results.csv`](../artifacts/post_lock_robustness/campaign_results.csv) | All 1,800 campaign-level outcomes and reward/fidelity fields |
| [`stress_escape_diagnostic.json`](../artifacts/post_lock_robustness/stress_escape_diagnostic.json) | Exact forensic summary of the single doubled-search escape |
| [`stress_escape_events.csv`](../artifacts/post_lock_robustness/stress_escape_events.csv) | Twelve event-level records from that campaign |
| [`stress_escape_summary.csv`](../artifacts/post_lock_robustness/stress_escape_summary.csv) | Compact campaign-level forensic summary |
| [`SHA256SUMS.txt`](../artifacts/post_lock_robustness/SHA256SUMS.txt) | Byte-level integrity hashes for every committed output |

The committed outputs are immutable evidence from the stated revision. Reproduction should be written to a separate output directory when preserving byte-level hashes is required.

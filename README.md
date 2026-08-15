# AegisLoop

**A self-evolving payment-threat digital twin.**

AegisLoop is a synthetic-only red-team/blue-team laboratory for emerging GenAI-enabled payment fraud. It identifies attack hypotheses, simulates stateful multi-event campaigns, lets a campaign-level LinUCB attacker learn valid evasions, and converts those evasions into hardening data for the next calibrated defender generation.

The final submission includes:

- a production-grade Next.js command center spanning Identify → Generate → Adapt → Defend;
- a reproducible Python simulator, attacker, defender and five-seed evaluation pipeline;
- an evidence-locked [solution walkthrough](./AegisLoop_Solution_Walkthrough.pdf);
- seven versioned evidence artifacts loaded and validated at runtime.

No real cardholder data, live payment endpoints or production payment systems are used.

## Evidence-backed result

Under the full fixed-budget protocol, the contextual bandit achieved mean reward **0.807 ± 0.457** (95% bootstrap CI **[0.519, 1.212]**) versus **0.126 ± 0.139** for random search and **0.503 ± 0.602** for rule mutation. It won all five paired seeds against both comparators (one-sided paired Wilcoxon **p=0.03125** for each).

Held-out-family ROC-AUC progressed from **0.9806 ± 0.0062** at V0 to **0.9938 ± 0.0049** at V1 and **0.99993 ± 0.00010** at V2. Against a matched, fixed action pool held constant across generations, V2 detected every campaign across five seeds. This is not an unqualified claim that V2 stops fresh attackers or production fraud.

The negative and boundary results are equally important: the novelty bonus did not improve reward (**p=0.625**), V1→V2 stability is directional rather than conclusive (**p=0.0625**), and V2 precision falls from **90.17%** at the experiment mix to **1.31%** after exact reweighting to 0.015% prevalence (**seed 20260812**).

See [RESULTS.md](./RESULTS.md) for the full protocol, confidence intervals and limitations.

## Run the final web prototype

Hosted production URL: **https://aegisloop-mcic-2026.vercel.app**

Requirements: Node.js 20+ and pnpm 10.

```powershell
pnpm install --frozen-lockfile
pnpm dev
```

Open `http://localhost:3000`. `run_demo.ps1` and `run_demo.sh` perform the same local web launch. The hosted deployment also exposes the isolated Python quick-benchmark function; its output is explicitly labeled illustrative and is never substituted for the archived full five-seed evidence.

## Verify

```powershell
pnpm lint
pnpm test
pnpm build
pnpm test:e2e
python -m pytest -q
```

The browser suite checks every product section against WCAG 2 A/AA rules at laptop viewport. Python tests cover the attack DSL, simulator determinism/fidelity, defender calibration, reward reconciliation and resilience guards.

## Repository map

- `src/app/` — nine-section Next.js product and evidence APIs.
- `src/components/` — command-center shell, interactive atlas, campaign timeline and charts.
- `src/lib/evidence/` — manifest, schemas and fail-closed artifact loader.
- `api/benchmark.py` — bounded hosted illustrative benchmark function.
- `src/aegisloop/` — simulator, attack DSL, attacker, defender and hardening loop.
- `experiments/` — full and quick reproducible benchmark runners.
- `artifacts/full_multiseed/` — immutable submission-grade five-seed evidence.
- `artifacts/precomputed/` — audits, prevalence evidence, diagnostics, attack atlas and representative rollout.
- `docs/` — architecture, benchmarks, threat model and responsible-use record.
- `tests/` and `tests-web/` — Python, data-contract, contrast and browser-accessibility tests.

The original Streamlit `app.py` remains as a legacy reference prototype; the Next.js command center is the final web artifact.

## Safety boundary

AegisLoop is an offline defensive simulator. Attack descriptions are abstract synthetic scenario parameters, not operational instructions. The system has no payment-rail connectors, rejects PII-like fields and exposes only versioned synthetic evidence.

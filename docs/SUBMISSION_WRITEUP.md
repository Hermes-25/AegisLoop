# AegisLoop â€” a self-evolving payment threat digital twin

**One sentence:** AegisLoop turns grounded GenAI fraud hypotheses into realistic,
stateful campaigns, lets a contextual-bandit attacker learn valid black-box evasions, and
uses every successful evasion to harden a calibrated payment decision engine.

## Overview

Static fraud tests answer â€œdoes this model catch attacks we already know?â€ AegisLoop asks
the harder question: â€œwhat will a learning adversary discover next, and does the defence
measurably improve after seeing those blind spots?â€ The result is a closed red-team/blue-team
lab covering Identify, Generate and Defend as one reproducible feedback loop.

## Identify â€” attacks researched

The threat compiler contains 32 grounded vectors grouped into eight executable archetypes
across eight channels and five rails:

- adaptive card-testing swarms;
- AI-personalised APP scams and mule networks;
- deepfake-assisted account takeover;
- synthetic-identity credit bust-out;
- agentic-commerce intent hijack;
- GenAI fake-merchant collusion;
- AI-crafted invoice and QR redirection; and
- synthetic-evidence refund abuse.

Each vector specifies the GenAI enabler, payment objective, entities, multi-event sequence,
safe simulation ranges and mitigation ideas. This becomes a machine-readable scenario DSL,
not a collection of chatbot answers.

## Generate â€” attack simulation

The payment digital twin creates a synthetic world of customers, cards/accounts, devices,
merchants and beneficiaries. Legitimate behaviour includes heterogeneous ticket sizes,
merchant risk, account tenure, cross-border propensity, device trust and time-of-day
patterns. Fraud is generated as 5â€“20 linked events, preserving campaign timing, velocity,
entity reuse, graph motifs, authentication changes, intent mismatch and evidence provenance.

A hard fidelity firewall runs before reward. It rejects missing fields, invalid values,
impossible amounts, non-chronological sequences, degenerate timing and implausible entity
structure. Distributional KS/JS diagnostics are reported separately; they are evidence, not
a loophole that lets unrealistic campaigns receive reward.

## Adapt â€” the learning red team

The attacker is a shared LinUCB contextual bandit. This is lightweight, explainable RL:
context contains recent black-box outcomes; the action is a complete campaign configuration;
and immediate reward combines approved fraud value, evasion rate, novelty and resource cost.
It never receives model weights or feature importance.

The defender remains frozen during a generation. This avoids moving-target confusion and
addresses the policy-oscillation risk documented in industrial payment-bandit research.

## Defend â€” detection and mitigation

The decision engine combines:

- histogram gradient boosting for tabular transaction risk;
- Isolation Forest anomaly scoring for unusual activity;
- temporal and velocity signals;
- card/customerâ€“deviceâ€“merchantâ€“beneficiary relationship features;
- agentic intent and evidence-provenance signals; and
- a calibrated operational policy: approve, step-up, hold or decline.

Reason codes explain unusual amount, velocity, relationship risk, intent mismatch,
provenance weakness and device risk. Successful V0 evasions become adversarial training
data for V1, which is then challenged by a fresh policy and newly sampled action space.

## Results and evaluation

The reproducible judge run uses a fixed seed, temporal legitimate-data splits,
campaign-disjoint fraud splits, four known families and four families held out entirely from
V0. Random, rule mutation and LinUCB receive the same frozen defender and campaign budget.

On the five-seed study:

- contextual-bandit mean reward: **0.501 Â± 0.759**;
- random-search mean reward: **âˆ’0.112 Â± 0.059**;
- bandit win rate versus random and rule mutation: **80%**;
- V0 held-out-family ROC-AUC: **0.989 Â± 0.006**;
- V1 held-out-family ROC-AUC: **0.999 Â± 0.001**;
- mean reduction in fresh-attacker approved value: **91.5% Â± 13.4%**; and
- legitimate FPR: **1.19% for V0 vs 1.13% for V1** on average.

These are synthetic-lab results, not production claims. Cross-paper AUC comparisons are
intentionally avoided because datasets and threat models differ.

## Novelty

The novelty is not â€œGPT for fraud search.â€ It is the combination of a campaign-level
learning adversary, stateful payment simulation, a realism firewall that prevents reward
hacking, and a falsifiable generation protocol showing that blind spots become measurable
defensive gain.

## Real-world feasibility

AegisLoop maps to an offline bank/network model-risk lab. Threat compilation, simulation,
red teaming and retraining occur offline. Nearline services compute velocity and graph
aggregates. The authorization path receives a compact calibrated risk score, reason codes
and mitigation action. The design is aligned with Mastercardâ€™s publicly described focus on
relationship risk, account/purchase/merchant/device context and precise real-time
decisioning, without claiming access to or replication of proprietary Mastercard systems.

## Responsible use

Only synthetic identifiers and events are used. There are no live endpoints, real cardholder
records or third-party targets. Scenarios are abstract and defensive. Random seeds,
configuration, provenance, tests and benchmark artifacts are included for auditability.



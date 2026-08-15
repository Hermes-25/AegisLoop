from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aegisloop.config import load_config
from aegisloop.experiment import run_benchmark, save_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the reproducible AegisLoop benchmark.")
    parser.add_argument("--config", default=str(ROOT / "config" / "default.yaml"))
    parser.add_argument("--output", default=str(ROOT / "artifacts" / "precomputed"))
    parser.add_argument("--quick", action="store_true", help="Use a smaller judge-demo workload.")
    args = parser.parse_args()
    artifacts = run_benchmark(load_config(args.config), quick=args.quick)
    save_artifacts(artifacts, args.output)
    summary = artifacts.summary
    bandit = summary["strategy_metrics"]["contextual_bandit"]
    random = summary["strategy_metrics"]["random"]
    print("AegisLoop benchmark complete")
    print(f"Bandit reward: {bandit['mean_reward']:.3f} vs random {random['mean_reward']:.3f}")
    print(f"Fresh-attacker value reduction after hardening: {summary['defender']['fresh_attacker_value_reduction']:.1%}")


if __name__ == "__main__":
    main()


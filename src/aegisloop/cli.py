from __future__ import annotations

import argparse
from pathlib import Path

from aegisloop.config import load_config
from aegisloop.experiment import run_benchmark, save_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(prog="aegisloop")
    parser.add_argument("--config", default="config/default.yaml")
    parser.add_argument("--output", default="artifacts/precomputed")
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    artifacts = run_benchmark(load_config(Path(args.config)), quick=args.quick)
    save_artifacts(artifacts, Path(args.output))


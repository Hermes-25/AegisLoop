from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "post_lock_robustness"


def test_post_lock_outputs_reconcile() -> None:
    with (ARTIFACTS / "campaign_results.csv").open(newline="", encoding="utf-8") as handle:
        campaigns = list(csv.DictReader(handle))
    with (ARTIFACTS / "run_summary.csv").open(newline="", encoding="utf-8") as handle:
        runs = list(csv.DictReader(handle))
    aggregate = json.loads((ARTIFACTS / "aggregate.json").read_text(encoding="utf-8"))
    diagnostic = json.loads(
        (ARTIFACTS / "stress_escape_diagnostic.json").read_text(encoding="utf-8")
    )

    independent = [row for row in campaigns if row["condition"] == "independent_pool"]
    stressed = [row for row in campaigns if row["condition"] == "double_search_pressure"]

    assert len(campaigns) == 1_800
    assert len(runs) == 20
    assert len(independent) == 1_080
    assert len(stressed) == 720
    assert all(row["valid"] == "True" for row in campaigns)
    assert all(float(row["detection_rate"]) == 1.0 for row in independent)
    assert sum(float(row["detection_rate"]) == 1.0 for row in stressed) == 719
    assert sum(float(row["approved_value"]) for row in independent) == 0.0
    assert math.isclose(
        sum(float(row["approved_value"]) for row in stressed),
        8.936488550668647,
        abs_tol=1e-12,
    )

    conditions = aggregate["conditions"]
    assert conditions["independent_pool"]["fully_detected_campaigns"] == 1_080
    assert conditions["double_search_pressure"]["fully_detected_campaigns"] == 719
    assert diagnostic["missed_events"] == 1
    assert math.isclose(diagnostic["approved_value"], 8.936488550668647, abs_tol=1e-12)


def test_post_lock_output_hashes() -> None:
    expected = {}
    for line in (ARTIFACTS / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, filename = line.split(maxsplit=1)
        expected[filename] = digest

    for filename, expected_digest in expected.items():
        actual = hashlib.sha256((ARTIFACTS / filename).read_bytes()).hexdigest()
        assert actual == expected_digest

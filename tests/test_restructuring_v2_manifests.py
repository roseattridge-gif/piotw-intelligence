from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "data/manifests"


def test_v2_manifests_are_deterministic_disjoint_and_temporal():
    subprocess.run([sys.executable, str(ROOT / "scripts/build_restructuring_v2_manifests.py")], check=True)
    development = list(csv.DictReader((MANIFESTS / "restructuring_development.csv").open()))
    validation = list(csv.DictReader((MANIFESTS / "restructuring_validation.csv").open()))
    holdout = list(csv.DictReader((MANIFESTS / "restructuring_holdout.csv").open()))
    assert len(development) == 20
    assert len(validation) == 191
    assert len(holdout) == 100
    assert len({row["stable_id"] for row in holdout}) == 100
    assert len({row["company"] for row in holdout}) == 100
    assert {row["cutoff"] for row in holdout} == {"2024-12-31"}
    assert {row["cutoff"] for row in validation} == {"2020-12-31", "2022-12-31"}
    development_keys = {(row["ticker"], row["cutoff"]) for row in development}
    assert not development_keys & {(row["ticker"], row["cutoff"]) for row in validation}
    assert not development_keys & {(row["ticker"], row["cutoff"]) for row in holdout}
    assert all(row["horizon_days"] == "365" and row["target"] == "restructuring_announced"
               for row in development + validation + holdout)

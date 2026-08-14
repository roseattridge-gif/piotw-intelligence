from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from validation.restructuring_v2_data import read_csv, validate_evidence

ROOT = Path(__file__).resolve().parents[1]


def test_reviewed_evidence_batch_is_reproducible_and_pre_cutoff():
    subprocess.run([sys.executable, str(ROOT / "scripts/build_restructuring_v2_evidence.py")],
                   check=True)
    manifest = []
    for partition in ("validation", "holdout"):
        manifest.extend(read_csv(ROOT / f"data/manifests/restructuring_{partition}.csv"))
    evidence = read_csv(ROOT / "data/restructuring_v2/evidence.csv")
    features = read_csv(ROOT / "data/restructuring_v2/features.csv")
    assert len(evidence) == len(features) == 27
    assert {row["occasion_id"] for row in evidence} == {row["occasion_id"] for row in features}
    assert all(row["availability_basis"] and row["availability_evidence"] for row in evidence)
    assert all(row["source_location"].startswith("p.") for row in evidence)
    validate_evidence(manifest, evidence, ROOT)
    for row in features:
        for field in ("pressure_language", "margin_pressure", "cash_pressure", "contrary_strength"):
            assert float(row[field]) * 20 == round(float(row[field]) * 20)

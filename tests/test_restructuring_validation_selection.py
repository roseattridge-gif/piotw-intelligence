import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_validation_cohort_is_reproducible_and_blind_to_pilot():
    subprocess.run([sys.executable, str(ROOT / "scripts/select_restructuring_validation.py")], check=True)
    rows = list(csv.DictReader((ROOT / "research/restructuring_validation_cohort.csv").open()))
    assert len(rows) == 10
    assert len({row["ticker"] for row in rows}) == 10
    assert {row["ticker"] for row in rows}.isdisjoint({"BOY", "CHG", "VSVS", "DWL"})
    assert [sum(row["stratum"] == group for row in rows) for group in
            ("aerospace_auto", "materials", "engineering_tech")] == [3, 3, 4]
    assert all(row["cutoff_1"] == "2021-12-31" and row["cutoff_2"] == "2022-12-31" for row in rows)


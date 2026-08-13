"""Select the blinded restructuring validation cohort without outcome inspection."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = "piotw-restructuring-validation-v1-2021-2022"
EXCLUDED = {
    "BOY": "used in exploratory pilot",
    "CHG": "used in exploratory pilot",
    "VSVS": "used in exploratory pilot",
    "DWL": "not an independently listed operating company at both cutoffs",
}
CUTOFFS = ("2021-12-31", "2022-12-31")

STRATA = {
    "aerospace_auto": {
        "Aerospace and defence", "Aerospace and automotive", "Automotive components",
        "Automotive testing", "Aerospace and engineering",
    },
    "materials": {"Industrial materials", "Specialty materials", "Building materials", "Advanced materials"},
}


def main() -> None:
    rows = list(csv.DictReader((ROOT / "research/cohort_candidates.csv").open()))
    all_subsectors = {row["subsector"] for row in rows}
    STRATA["engineering_tech"] = all_subsectors - STRATA["aerospace_auto"] - STRATA["materials"]
    quotas = {"aerospace_auto": 3, "materials": 3, "engineering_tech": 4}
    selected: list[dict[str, str]] = []
    for stratum, subsectors in STRATA.items():
        eligible = []
        for row in rows:
            if row["ticker"] in EXCLUDED or row["subsector"] not in subsectors:
                continue
            digest = hashlib.sha256(f"{SEED}:{row['selection_key']}".encode()).hexdigest()
            eligible.append({"stratum": stratum, **row, "selection_hash": digest})
        selected.extend(sorted(eligible, key=lambda row: row["selection_hash"])[:quotas[stratum]])

    output = ROOT / "research/restructuring_validation_cohort.csv"
    fields = ["stratum", "company", "ticker", "subsector", "selection_key", "selection_hash", "cutoff_1", "cutoff_2"]
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in selected:
            writer.writerow({**row, "cutoff_1": CUTOFFS[0], "cutoff_2": CUTOFFS[1]})
    print(f"selected {len(selected)} companies and {len(selected) * len(CUTOFFS)} prediction occasions")
    for row in selected:
        print(f"{row['stratum']}: {row['company']} ({row['ticker']}) {row['selection_hash'][:12]}")


if __name__ == "__main__":
    main()


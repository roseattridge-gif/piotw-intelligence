"""Select the pilot reproducibly without reference to outcomes."""
import csv
import hashlib
from pathlib import Path

SEED = "piotw-pilot-v0.1-2021-12-31"
ROOT = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader((ROOT / "research/cohort_candidates.csv").open()))
for row in rows:
    row["hash"] = hashlib.sha256(f"{SEED}:{row['selection_key']}".encode()).hexdigest()

# Take the lowest hash within three broad strata to avoid a single-subsector pilot.
strata = {
    "aerospace_auto": {"Aerospace and defence", "Aerospace and automotive", "Automotive components", "Automotive testing", "Aerospace and engineering"},
    "materials": {"Industrial materials", "Specialty materials", "Building materials", "Advanced materials"},
    "engineering_tech": {r["subsector"] for r in rows} - {"Aerospace and defence", "Aerospace and automotive", "Automotive components", "Automotive testing", "Aerospace and engineering", "Industrial materials", "Specialty materials", "Building materials", "Advanced materials"},
}
selected = []
for stratum, subsectors in strata.items():
    eligible = [r for r in rows if r["subsector"] in subsectors]
    pick = min(eligible, key=lambda r: r["hash"])
    selected.append({"stratum": stratum, **pick})

out = ROOT / "research/pilot_selection.csv"
with out.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["stratum", "company", "ticker", "subsector", "selection_key", "hash"])
    writer.writeheader(); writer.writerows(selected)
print("\n".join(f"{x['stratum']}: {x['company']} ({x['ticker']}) {x['hash'][:12]}" for x in selected))

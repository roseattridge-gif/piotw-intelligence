"""Fail fast if the retained pilot loses provenance or leakage safeguards."""
import csv, hashlib, json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = list(csv.DictReader((ROOT / "data/document_manifest.csv").open()))
assert len(manifest) == 7
for row in manifest:
    path = ROOT / row["raw_storage_path"]
    assert path.exists(), path
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row["content_hash"], path
    assert row["published_at"] and row["available_at"] and row["retrieved_at"]
    if row["role"] == "prediction": assert date.fromisoformat(row["available_at"]) <= date(2021,12,31)
    else: assert date.fromisoformat(row["available_at"]) > date(2021,12,31)
ledger = list(csv.DictReader((ROOT / "data/evidence_ledger.csv").open()))
assert len(ledger) == 24
assert all(row["validation_status"] == "manual_checked" and row["source_location"] for row in ledger)
results = json.loads((ROOT / "data/derived/pilot_results.json").read_text())
assert results["metrics"]["PIOTW operational"]["brier"] > results["metrics"]["Inventory/revenue divergence"]["brier"]
print("pilot provenance, cutoff, evidence and gate-decision checks passed")

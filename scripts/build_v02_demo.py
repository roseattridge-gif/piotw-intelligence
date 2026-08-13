"""Re-express the checked v0.1 facts through the v0.2 architecture.

This is an integration demonstration, not a new backtest: it uses the same tiny retrospective evidence.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from intelligence.models import EvidenceObservation, SourceCoverage
from intelligence.scoring.evidence_model import EvidenceModel

AS_OF = date(2021, 12, 31)

FEATURE_MAP = {
    "commercial_weakness": ("financial_state", "guidance_change"),
    "margin": ("financial_state", "margin_change"),
    "cash_generation": ("financial_state", "cash_conversion_change"),
    "working_capital": ("financial_state", "inventory_revenue_divergence"),
    "supply_constraint": ("operational_disclosure", "supplier_constraint"),
    "cost_base_inflation": ("operational_disclosure", "delivery_constraint"),
    "execution_recovery": ("operational_disclosure", "restructuring_productivity"),
    "forecasting_weakness": ("operational_disclosure", "narrative_contradiction"),
    "inventory_build": ("operational_disclosure", "working_capital_language"),
    "capacity_constraint": ("capacity_footprint", "capacity_investment"),
}


def load() -> tuple[list[EvidenceObservation], list[SourceCoverage]]:
    manifests = {row["document_id"]: row for row in csv.DictReader((ROOT / "data/document_manifest.csv").open())}
    observations: list[EvidenceObservation] = []
    companies: set[str] = set()
    for row in csv.DictReader((ROOT / "data/evidence_ledger.csv").open()):
        companies.add(row["company"])
        family, feature = FEATURE_MAP[row["signal_family"]]
        manifest = manifests[row["document_id"]]
        direction = float(row["direction"])
        is_capacity = feature == "capacity_investment"
        observations.append(EvidenceObservation(
            observation_id=row["fact_id"], company_id=row["company"], family=family, feature=feature,
            event_date=date.fromisoformat(manifest["available_at"]),
            available_at=datetime.fromisoformat(manifest["available_at"]).replace(tzinfo=timezone.utc),
            source_type="company_regulated_disclosure", source_url=manifest["source_url"],
            source_name=f"{row['company']} official disclosure", source_is_company_controlled=True,
            event_cluster_id=row["document_id"], direction_pressure=direction,
            direction_expansion=(1 if is_capacity and direction > 0 else -0.25 if direction > 0 else 0.35),
            strength=float(row["strength"]), source_reliability=float(row["reliability"]),
            measurement_quality=1.0, materiality=float(row["materiality"]),
            independence=float(row["independence"]), relevance_pressure=float(row["relevance"]),
            relevance_expansion=float(row["relevance"]), raw_value=row["observation"],
            explanation=row["observation"], extraction_method="manual_checked_v01_migration",
            validation_status=row["validation_status"],
        ))
    coverage = []
    for company in companies:
        for family, value, note in [
            ("operational_disclosure", 0.35, "One retained pre-cutoff disclosure; not complete history"),
            ("capacity_footprint", 0.25, "Capacity facts only from one retained disclosure"),
            ("financial_state", 0.50, "Selected financial facts, not two-year feature history"),
        ]:
            coverage.append(SourceCoverage(company_id=company, family=family, as_of_date=AS_OF,
                                           coverage=value, note=note))
    return observations, coverage


def main() -> None:
    observations, coverage = load()
    scorer = EvidenceModel(ROOT / "intelligence/ontology/signal_weights_v02.yaml",
                           ROOT / "intelligence/ontology/signal_catalog_v02.yaml")
    predictions = []
    priors = {6: 0.10, 12: 0.15, 18: 0.20}
    for company in sorted({item.company_id for item in observations}):
        for model in ("operational_pressure", "expansion_transformation"):
            for horizon in (6, 12, 18):
                predictions.append(scorer.predict(company, model, horizon, AS_OF, observations, coverage,
                                                  prior_probability=priors[horizon]))
    result = {
        "status": "architecture integration demo using the existing retrospective v0.1 evidence; not a new validation",
        "as_of_date": AS_OF.isoformat(),
        "model_version": scorer.version,
        "predictions": [row.model_dump(mode="json") for row in predictions],
    }
    target = ROOT / "data/derived/pilot_v02_demo.json"
    target.write_text(json.dumps(result, indent=2))
    print(f"wrote {len(predictions)} predictions to {target}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from piotw_read_model.company_intelligence import DIMENSIONS, CompanyIntelligenceSnapshot, build_careers_profile

COMPANIES = {
    "affirm": "Affirm", "cloudflare": "Cloudflare", "datadog": "Datadog",
    "duolingo": "Duolingo", "linear": "Linear", "mongodb": "MongoDB",
    "notion": "Notion", "palantir": "Palantir", "robinhood": "Robinhood",
    "samsara": "Samsara", "toast": "Toast",
}


def main() -> None:
    output = ROOT / "data/derived/company_intelligence_v1"
    output.mkdir(parents=True, exist_ok=True)
    web_output = ROOT / "piotw-web/data/company-intelligence"
    web_output.mkdir(parents=True, exist_ok=True)
    for company_id, display_name in COMPANIES.items():
        snapshot = build_careers_profile(ROOT / "data/collection/careers_v1/careers_longitudinal.sqlite3",
            company_id=company_id, display_name=display_name, as_of=datetime.now(UTC))
        serialized = snapshot.model_dump_json(indent=2) + "\n"
        (output / f"{company_id}.json").write_text(serialized)
        (web_output / f"{company_id}.json").write_text(serialized)
    database = ROOT / "data/collection/careers_v1/careers_longitudinal.sqlite3"
    with sqlite3.connect(database) as connection:
        provider, next_due, failures, health = connection.execute(
            "SELECT provider,next_eligible_fetch,consecutive_failures,health FROM career_source_state WHERE company_id='anduril'"
        ).fetchone()
    unavailable = {
        "schema_version": "company-intelligence-snapshot-v1", "company_id": "anduril", "display_name": "Anduril",
        "observation_date": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "dimensions": [{"dimension_id": identifier, "name": name, "coverage_status": "INSUFFICIENT_SOURCE_COVERAGE", "observations": [], "accepted_events": [], "score": {"status": "NOT_YET_VALIDATED", "value": None}} for identifier, name in DIMENSIONS],
        "source_freshness": [{"source_family": "careers_ats", "source_adapter": provider, "last_successful_fetch": None, "next_due_collection": next_due, "consecutive_failures": failures, "health": health}, {"source_family": "contracts_procurement", "health": "COLLECTING_UNRESOLVED", "company_attachment": "NO_APPROVED_ENTITY_MATCH"}],
        "data_coverage": {"careers_snapshots": 0, "new": 0, "absent": 0, "closed": 0, "reopened": 0, "procurement_company_records": 0, "source_families_missing": ["careers_ats", "issuer_reporting"], "stale_sources": 0, "failed_sources": 1, "coverage_note": "Careers collection failed; procurement suppliers remain unresolved."},
        "prediction": {"status": "NOT_YET_VALIDATED", "value": None}, "overall_score": {"status": "NOT_YET_VALIDATED", "value": None}, "benchmark": {"status": "NOT_YET_VALIDATED", "value": None}, "pressure": {"status": "NOT_YET_VALIDATED", "value": None}, "expansion": {"status": "NOT_YET_VALIDATED", "value": None}, "careers_history": []
    }
    serialized = json.dumps(unavailable, indent=2) + "\n"
    (output / "anduril.json").write_text(serialized)
    (web_output / "anduril.json").write_text(serialized)
    (ROOT / "config/company_intelligence_snapshot_v1.schema.json").write_text(
        json.dumps(CompanyIntelligenceSnapshot.model_json_schema(), indent=2, sort_keys=True) + "\n")
    print(f"wrote {len(COMPANIES) + 1} company snapshots to {output}")


if __name__ == "__main__":
    main()

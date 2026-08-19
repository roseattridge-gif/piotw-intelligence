from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from piotw_orchestrator import UnknownCompanyOrchestrator


def main() -> int:
    cutoff = datetime.fromisoformat("2026-08-19T00:00:00+00:00")
    companies = ["cloudflare", "affirm", "samsara", "anduril", "datadog", "mongodb"]
    engine = UnknownCompanyOrchestrator()
    rows = []
    for company in companies:
        result = engine.build(company=company, as_of=cutoff)
        careers = next(item for item in result.manifest.source_availability
                       if item.source_family == "careers_ats")
        rows.append({
            "company_id": company,
            "source_coverage": {item.source_family: item.status
                                for item in result.manifest.source_availability},
            "history_depth": careers.record_count,
            "factual_observations": len(result.intelligence.evidence),
            "condition_candidates": len(result.qualifications),
            "qualifications": [{
                "candidate_type": item.condition_candidate_type,
                "status": item.qualification_status,
                "tests": {test.test_id: test.status for test in item.tests},
                "failed_tests": item.failed_tests,
                "history": item.history.model_dump(mode="json"),
                "magnitude": item.magnitude.model_dump(mode="json"),
                "persistence": item.persistence.model_dump(mode="json"),
                "corroboration": item.corroboration.model_dump(mode="json"),
                "entity_scope_valid": item.entity_scope_valid,
                "data_quality": item.data_quality.model_dump(mode="json"),
                "explanation": item.human_readable_explanation,
            } for item in result.qualifications],
            "qualified_conditions": len(result.intelligence.conditions),
            "detect_status": result.intelligence.capabilities.detect,
            "source_reason": careers.reason,
        })
    output = {
        "schema_version": "piotw-condition-qualification-development-results-v0.1",
        "policy_version": engine.condition_engine.policy["policy_version"],
        "scientifically_validated": False,
        "analysis_cutoff": cutoff.isoformat(),
        "companies": rows,
        "summary": {
            "companies_tested": len(rows),
            "candidate_conditions": sum(row["condition_candidates"] for row in rows),
            "qualified_conditions": sum(row["qualified_conditions"] for row in rows),
            "insufficient_evidence": sum(
                item["status"] == "INSUFFICIENT_EVIDENCE"
                for row in rows for item in row["qualifications"]),
        },
    }
    path = ROOT / "data/derived/piotw_condition_qualification_v0_1_results.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

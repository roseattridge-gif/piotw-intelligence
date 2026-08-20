#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from piotw_orchestrator import UnknownCompanyOrchestrator

OUTPUT = ROOT / "data/derived/piotw_multi_source_evidence_depth_v0_1_results.json"
CUTOFF = datetime(2026, 8, 19, tzinfo=UTC)


def main() -> None:
    engine = UnknownCompanyOrchestrator()
    rows = []
    for company_id in ("travis-perkins", "cloudflare"):
        result = engine.build(company=company_id, as_of=CUTOFF)
        persisted = result
        rows.append({
            "company_id": company_id,
            "run_id": persisted.run_id,
            "evidence_count": persisted.intelligence.coverage.evidence_count,
            "families_present": persisted.intelligence.coverage.source_families_present,
            "families_missing": persisted.intelligence.coverage.source_families_missing,
            "coverage_matrix": persisted.manifest.evidence_family_coverage,
            "qualifications": [{
                "candidate_type": item.condition_candidate_type,
                "status": item.qualification_status,
                "failed_tests": item.failed_tests,
                "evidence_families": item.evidence_families,
            } for item in persisted.qualifications],
            "qualified_conditions": [item.model_dump(mode="json") for item in persisted.intelligence.conditions],
            "capabilities": persisted.intelligence.capabilities.model_dump(mode="json"),
        })
    payload = {
        "schema_version": "piotw-multi-source-evidence-depth-results-v0.1",
        "generated_at": CUTOFF.isoformat(),
        "scientific_gate_run": False,
        "scientifically_validated": False,
        "companies": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

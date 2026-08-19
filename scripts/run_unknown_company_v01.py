from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from piotw_orchestrator import UnknownCompanyOrchestrator


def main() -> int:
    parser = argparse.ArgumentParser(description="Build one cutoff-safe PIOTW company object from approved stored evidence.")
    parser.add_argument("--company", required=True, help="Approved company ID or exact company name")
    parser.add_argument("--as-of", required=True, help="Analysis cutoff as ISO-8601 timestamp")
    parser.add_argument("--entity-id", help="Optional explicit approved entity/company ID")
    parser.add_argument("--no-web", action="store_true", help="Do not publish the object to the generic frontend data directory")
    args = parser.parse_args()
    orchestrator = UnknownCompanyOrchestrator()
    result = orchestrator.build(
        company=args.company,
        as_of=datetime.fromisoformat(args.as_of),
        explicit_entity_id=args.entity_id,
    )
    result = orchestrator.persist(result, publish_to_web=not args.no_web)
    summary = {"run_id":result.run_id,"company_id":result.intelligence.company.company_id,
        "as_of":result.intelligence.as_of.isoformat(),"sources":{item.source_family:item.status for item in result.manifest.source_availability},
        "evidence_count":len(result.intelligence.evidence),"conditions":len(result.intelligence.conditions),
        "condition_candidates":len(result.qualifications),
        "qualification_statuses":[item.qualification_status for item in result.qualifications],
        "capabilities":result.intelligence.capabilities.model_dump(),"manifest_path":result.manifest_path,
        "intelligence_path":result.intelligence_path,"qualifications_path":result.qualifications_path,
        "web_path":result.web_path,
        "manual_intervention_required":result.manual_intervention_required}
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

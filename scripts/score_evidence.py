from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from intelligence.io import read_jsonl
from intelligence.models import EvidenceObservation, SourceCoverage
from intelligence.scoring.evidence_model import EvidenceModel


def main() -> None:
    parser = argparse.ArgumentParser(description="Score point-in-time evidence with the transparent v0.2 model")
    parser.add_argument("company_id")
    parser.add_argument("--observations", required=True)
    parser.add_argument("--coverage", required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--model", choices=["operational_pressure", "expansion_transformation"], required=True)
    parser.add_argument("--horizon", type=int, choices=[6, 12, 18], default=18)
    parser.add_argument("--prior", type=float, default=0.20)
    args = parser.parse_args()
    scorer = EvidenceModel(ROOT / "intelligence/ontology/signal_weights_v02.yaml",
                           ROOT / "intelligence/ontology/signal_catalog_v02.yaml")
    result = scorer.predict(
        args.company_id, args.model, args.horizon, date.fromisoformat(args.as_of),
        read_jsonl(args.observations, EvidenceObservation), read_jsonl(args.coverage, SourceCoverage),
        args.prior,
    )
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()

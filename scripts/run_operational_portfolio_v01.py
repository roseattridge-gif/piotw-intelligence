from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from piotw_orchestrator.portfolio_v01 import PortfolioOrchestrator


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/portfolios/real_development_portfolio_v0_1.json")
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--previous")
    args = parser.parse_args()
    orchestrator = PortfolioOrchestrator()
    config = orchestrator.load_config(args.config)
    previous = json.loads(Path(args.previous).read_text()) if args.previous else None
    result = orchestrator.persist(orchestrator.run(config, as_of=datetime.fromisoformat(args.as_of), previous=previous))
    print(json.dumps({"run_id": result.run_id, "run_path": result.run_path, "web_path": result.web_path}, indent=2))


if __name__ == "__main__":
    main()

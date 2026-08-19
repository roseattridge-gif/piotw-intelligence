from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_1.pipeline import run_demo

if __name__ == "__main__":
    result = run_demo(ROOT)
    print(json.dumps({
        "engine_version": result["engine_version"],
        "corpus": result["corpus"],
        "quality": result["quality"],
        "performance": result["performance"],
        "output": "data/derived/evidence_engine_v0_1/demo_output.json",
    }, indent=2))


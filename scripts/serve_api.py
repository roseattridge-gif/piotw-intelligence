from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.api import serve


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serve the read-only local PIOTW API")
    parser.add_argument("--database", default="data/derived/piotw_mvp.sqlite3")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    serve(args.database, port=args.port)

from __future__ import annotations

import argparse
import sys
from datetime import UTC, date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipelines.procurement.find_a_tender import FindATenderAdapter, resolve_supplier
from pipelines.procurement.storage import persist_records


def main() -> None:
    parser = argparse.ArgumentParser(description="Persist one idempotent daily Find a Tender OCDS collection")
    parser.add_argument("--date", default=datetime.now(UTC).date().isoformat())
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--database", default=str(ROOT / "data/collection/procurement/find_a_tender.sqlite3"))
    args = parser.parse_args()
    day = date.fromisoformat(args.date)
    records = FindATenderAdapter().collect(day, day, limit=args.limit)
    resolutions = {row.supplier_raw_name: resolve_supplier(row.supplier_raw_name, {})
                   for row in records if row.supplier_raw_name}
    result = persist_records(args.database, records, fetched_at=datetime.now(UTC), resolutions=resolutions)
    print({**result, "records": len(records), "cadence": "DAILY"})


if __name__ == "__main__":
    main()

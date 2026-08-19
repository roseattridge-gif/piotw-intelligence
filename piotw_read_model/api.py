from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_company_snapshot(snapshot_directory: str | Path, company_id: str) -> dict[str, Any]:
    """Return the versioned internal read model; it contains no inferred scores."""
    path = Path(snapshot_directory) / f"{company_id}.json"
    if not path.is_file():
        raise KeyError(f"unknown company snapshot: {company_id}")
    return json.loads(path.read_text())

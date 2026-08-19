from __future__ import annotations

import hashlib
import json
from pathlib import Path


def verify_frozen_isolation(root: str | Path) -> dict[str, str]:
    root = Path(root)
    guard = json.loads((root / "config/evidence/frozen_rules_1_0_0_guard.json").read_text())
    actual = {}
    for relative, expected in guard["files"].items():
        digest = hashlib.sha256((root / relative).read_bytes()).hexdigest()
        if digest != expected:
            raise RuntimeError(f"frozen Rules 1.0.0 artefact changed: {relative}")
        actual[relative] = digest
    lock = json.loads((root / "config/frozen/restructuring_v2_lock.json").read_text())
    if lock["model_specification_sha256"] != guard["model_specification_sha256"]:
        raise RuntimeError("frozen model specification hash changed")
    return actual


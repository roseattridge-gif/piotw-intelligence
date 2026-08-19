from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "reviewer_pack_human_ambiguity_v1"
INTERNAL = PACK / "internal_do_not_share"
MANIFEST = INTERNAL / "pack_freeze_manifest.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if MANIFEST.exists():
        raise RuntimeError("review pack is already frozen; alteration or refreeze is prohibited")
    membership = json.loads((INTERNAL / "frozen_36_case_membership.json").read_text())
    a = json.loads((PACK / "reviewer_A/order_manifest.json").read_text())
    b = json.loads((PACK / "reviewer_B/order_manifest.json").read_text())
    if set(a["case_ids_in_order"]) != set(b["case_ids_in_order"]) or a["case_ids_in_order"] == b["case_ids_in_order"]:
        raise RuntimeError("reviewer packs must have identical membership and independent orderings")
    files = {}
    for path in sorted(PACK.rglob("*")):
        if path.is_file() and path != MANIFEST:
            files[str(path.relative_to(PACK))] = sha(path)
    canonical = "\n".join(f"{path}:{digest}" for path, digest in files.items()).encode()
    payload = {
        "pack_version": "piotw-human-ambiguity-review-v1",
        "frozen_at": datetime.now(UTC).isoformat(),
        "case_count": membership["case_count"],
        "membership_sha256": sha(INTERNAL / "frozen_36_case_membership.json"),
        "file_count": len(files),
        "files": files,
        "pack_sha256": hashlib.sha256(canonical).hexdigest(),
        "answers_present": False,
        "formal_gold": False,
        "outcomes_accessed": False,
    }
    MANIFEST.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"pack_sha256": payload["pack_sha256"], "file_count": len(files)}, indent=2))


if __name__ == "__main__":
    main()

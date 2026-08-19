from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reviewer_pack_v0_3_7_independent"
DESTINATION = ROOT / "reviewer_pack_v0_3_7_independent_blinded"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if not SOURCE.exists():
        raise RuntimeError("Frozen source pack is missing")
    DESTINATION.mkdir(exist_ok=True)
    for reviewer in ("reviewer_A", "reviewer_B"):
        target = DESTINATION / reviewer
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(SOURCE, target)
    files = sorted(path for path in DESTINATION.rglob("*") if path.is_file())
    for path in files:
        relative = str(path.relative_to(DESTINATION)).casefold()
        if any(token in relative for token in ("derived", "candidate", "model_output", "provider_response", "answer_key")):
            raise RuntimeError(f"Machine-answer artefact found in blinded pack: {path}")
    manifest = {
        "study": "evidence_engine_v0_3_7_independent_atomic_observation_validation",
        "status": "BLINDED_PACKS_FROZEN_AWAITING_REVIEW",
        "frozen_at": datetime.now(UTC).isoformat(),
        "reviewers": ["reviewer_A", "reviewer_B"],
        "formal_gold": False,
        "scientific_gate_run": False,
        "files": {str(path.relative_to(DESTINATION)): digest(path) for path in files},
    }
    manifest_path = DESTINATION / "blinded_pack_freeze_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"files": len(files), "manifest_sha256": digest(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()

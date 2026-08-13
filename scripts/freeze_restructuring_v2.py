"""Hash and validate every v2 specification before new outcome review."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from validation.restructuring_v2 import BASELINES_PATH, MODEL_PATH, specification_hash

OUTPUT = ROOT / "config/frozen/restructuring_v2_lock.json"
DOCUMENTS = [
    ROOT / "docs/restructuring-validation-v2-plan.md",
    ROOT / "docs/restructuring-outcome-protocol-v2.md",
    ROOT / "docs/restructuring-cohort-v2.md",
    ROOT / "docs/restructuring-validation-gate-v2.md",
]
MANIFESTS = [
    ROOT / "research/restructuring_v2_candidate_universe.csv",
    ROOT / "data/manifests/restructuring_development.csv",
    ROOT / "data/manifests/restructuring_validation.csv",
    ROOT / "data/manifests/restructuring_holdout.csv",
]
FROZEN_AT = "2026-08-13T20:15:00+01:00"


def git_head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout.strip()


def sha256_bytes(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    for path in [MODEL_PATH, BASELINES_PATH, *DOCUMENTS, *MANIFESTS]:
        if not path.exists():
            raise FileNotFoundError(path)
    result = {
        "lock_version": "restructuring-validation-v2.0.0",
        "frozen_at": FROZEN_AT,
        "recorded_from_git_commit": git_head(),
        "model_version": "restructuring-rules-1.0.0",
        "model_specification_sha256": specification_hash(MODEL_PATH),
        "baseline_set_version": "restructuring-baselines-v2.0.0",
        "baseline_specification_sha256": specification_hash(BASELINES_PATH),
        "document_sha256": {str(path.relative_to(ROOT)): sha256_bytes(path) for path in DOCUMENTS},
        "manifest_sha256": {str(path.relative_to(ROOT)): sha256_bytes(path) for path in MANIFESTS},
        "outcomes_inspected_for_v2": False,
        "generated_at_note": "Timestamp fixed as part of the protocol; regeneration is deterministic except recorded_from_git_commit.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"locked model {result['model_specification_sha256'][:12]} and baselines {result['baseline_specification_sha256'][:12]}")
    return result


if __name__ == "__main__":
    build()

import json
from pathlib import Path

from scripts.freeze_restructuring_v2 import verify

ROOT = Path(__file__).resolve().parents[1]


def test_committed_v2_lock_matches_every_frozen_input():
    locked = verify()
    assert locked == json.loads((ROOT / "config/frozen/restructuring_v2_lock.json").read_text())
    assert locked["outcomes_inspected_for_v2"] is False

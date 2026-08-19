import json
from pathlib import Path

import pytest

from scripts.run_evidence_v035_fresh_gate import assert_frozen_inputs, ensure_one_run

ROOT = Path(__file__).resolve().parents[1]


def test_fresh_corpus_and_gold_freezes_are_stable_and_separate_from_human_gold():
    candidates, labels = assert_frozen_inputs()
    manifest = (ROOT / "data/evidence_engine_v0_3_5/fresh_corpus_manifest.csv").read_text()
    assert len(candidates) == len(labels) == 156
    assert manifest.count("external_us_fresh_no_outcomes") == 10
    assert all(row["formal_independent_human_gold"] == "false" for row in labels)
    assert all(row["admissible_for_model2_gate"] == "false" for row in labels)


def test_one_run_enforcement_fails_closed_when_ledger_exists(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger.json"; ledger.write_text(json.dumps({"run_count": 1}))
    monkeypatch.setattr("scripts.run_evidence_v035_fresh_gate.LEDGER", ledger)
    with pytest.raises(RuntimeError, match="prohibits rerun"):
        ensure_one_run()

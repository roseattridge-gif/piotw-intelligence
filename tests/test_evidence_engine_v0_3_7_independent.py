import csv
import json
from pathlib import Path

from scripts.prepare_evidence_v037_independent_validation import ISSUERS, prior_values

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/evidence_engine_v0_3_7_independent"


def test_fixed_issuers_are_absent_from_prior_manifests():
    companies, tickers, _, _ = prior_values()
    for company, ticker, _ in ISSUERS:
        assert company.casefold() not in companies
        assert ticker.casefold() not in tickers


def test_protocol_freezes_gate_and_one_run_rule():
    protocol = (ROOT / "docs/evidence-engine-v0.3.7-independent-validation-protocol.md").read_text()
    assert "observation precision >= 0.90" in protocol
    assert "supported-observation recall >= 0.80" in protocol
    assert "evidence-zone recall >= 0.90" in protocol
    assert "severe false positives = 0" in protocol
    assert "one model execution only" in protocol


def test_blank_labels_have_no_machine_answers():
    rows = list(csv.DictReader((DATA / "blank_atomic_observations.csv").open()))
    assert rows == []


def test_frozen_corpus_is_complete_and_contamination_free_when_present():
    manifest = DATA / "corpus_manifest.csv"
    if not manifest.exists():
        return
    rows = list(csv.DictReader(manifest.open()))
    assert len(rows) == 20
    assert len({row["company"] for row in rows}) == 10
    assert all(Path(ROOT / row["local_artifact"]).exists() for row in rows)
    checks = json.loads((DATA / "contamination_check.json").read_text())
    assert checks["status"] == "PASS"
    assert all(row["passed"] for row in checks["checks"])
    freeze = json.loads((DATA / "corpus_freeze_manifest.json").read_text())
    assert freeze["scientific_gate_run"] is False
    assert freeze["formal_independent_human_gold_available"] is False
    assert freeze["one_run_remaining"] == 1

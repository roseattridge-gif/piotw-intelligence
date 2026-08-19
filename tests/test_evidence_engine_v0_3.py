from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from evidence_engine_v0_1.guard import verify_frozen_isolation
from evidence_engine_v0_3.blinding import freeze_annotations, verify_frozen_annotations
from evidence_engine_v0_3.visual_tables import extract_table_observations, parse_number

ROOT = Path(__file__).resolve().parents[1]


def test_visual_table_metric_identity_period_scale_and_basis():
    html = """<table><tr><th>USD in millions</th><th>2024</th><th>2023</th></tr>
    <tr><td>Adjusted EBITDA</td><td>$120</td><td>$100</td></tr>
    <tr><td>Operating margin</td><td>8.4%</td><td>11.2%</td></tr></table>"""
    rows = extract_table_observations(html)
    assert [(row.metric, row.value, row.period, row.accounting_basis) for row in rows] == [
        ("adjusted_ebitda", 120_000_000, "2024", "adjusted"),
        ("adjusted_ebitda", 100_000_000, "2023", "adjusted"),
        ("operating_margin", 8.4, "2024", "statutory_or_reported"),
        ("operating_margin", 11.2, "2023", "statutory_or_reported"),
    ]


def test_net_debt_and_net_cash_remain_distinct_and_brackets_are_negative():
    html = """<table><tr><th>GBP in millions</th><th>2024</th></tr>
    <tr><td>Net debt</td><td>£44</td></tr><tr><td>Net cash</td><td>(£12)</td></tr></table>"""
    values = {row.metric: row.value for row in extract_table_observations(html)}
    assert values == {"net_debt": 44_000_000, "net_cash": -12_000_000}
    assert parse_number("(1,250)") == -1250


def test_blind_freeze_refuses_empty_annotations(tmp_path: Path):
    source = ROOT / "data/evidence_engine_v0_3"
    for name in ("gold_observations.csv", "gold_events.csv"):
        (tmp_path / name).write_text((source / name).read_text())
    with pytest.raises(ValueError, match="empty"):
        freeze_annotations(tmp_path, "reviewer-1")


def test_frozen_gold_detects_post_freeze_mutation(tmp_path: Path):
    observation_fields = ["document_id", "metric_type", "value", "unit", "scale", "currency",
        "period", "accounting_basis", "source_page_section", "exact_evidence_span", "reviewer_id",
        "annotation_timestamp", "ambiguity_flag"]
    event_fields = ["document_id", "reviewer_free_text_label", "mapped_event_type", "label_status",
        "source_page_section", "exact_evidence_span", "reviewer_id", "annotation_timestamp", "ambiguity_flag"]
    for name, fields in (("gold_observations.csv", observation_fields), ("gold_events.csv", event_fields)):
        with (tmp_path / name).open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fields); writer.writeheader()
            writer.writerow({field: ({"reviewer_id": "r", "annotation_timestamp": "2026-01-01T00:00:00Z",
                "exact_evidence_span": "source text"}.get(field, "x")) for field in fields})
    freeze_annotations(tmp_path, "r")
    verify_frozen_annotations(tmp_path)
    (tmp_path / "gold_events.csv").write_text((tmp_path / "gold_events.csv").read_text() + "tampered")
    with pytest.raises(ValueError, match="changed"):
        verify_frozen_annotations(tmp_path)


def test_corpus_is_external_blinded_and_pdf_backed():
    rows = list(csv.DictReader((ROOT / "data/evidence_engine_v0_3/corpus_manifest.csv").open()))
    assert len(rows) == 30 and len({row["ticker"] for row in rows}) == 15
    assert all(row["development_safe_status"] == "external_us_development_no_outcomes" for row in rows)
    assert all((ROOT / row["reviewer_pdf"]).exists() for row in rows)
    assert {row["annotation_workflow"] for row in rows} == {
        "human_first", "piotw_first_review_burden_only"}


def test_pre_evaluation_result_is_honest_and_rules_remain_protected():
    result = json.loads((ROOT / "data/derived/evidence_engine_v0_3_results.json").read_text())
    assert result["status"] == "NOT READY"
    assert result["evaluation_stage"] == "pre_evaluation_blocked"
    assert result["metrics"]["overall_numerical_accuracy"]["total"] == 0
    assert not result["outcomes_used"] and not result["predictive_model_trained"]
    assert len(verify_frozen_isolation(ROOT)) == 12

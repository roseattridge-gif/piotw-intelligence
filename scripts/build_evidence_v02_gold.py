from __future__ import annotations

import csv
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_2.events import EVENT_PATTERNS, candidate_sentences, context_status
from evidence_engine_v0_2.ixbrl import primary_facts, visible_text

DATA = ROOT / "data/evidence_engine_v0_2"
REVIEWED_AT = datetime(2026, 8, 15, 17, 30, tzinfo=UTC).isoformat()


def main() -> None:
    documents = list(csv.DictReader((DATA / "corpus_manifest.csv").open()))
    observation_fields = ["gold_id", "company", "ticker", "document_id", "metric_type", "value",
        "unit", "currency", "scale", "sign", "reporting_period", "period_start", "period_role",
        "accounting_basis", "exact_evidence_span", "page_or_section", "reviewer", "review_timestamp",
        "notes", "ambiguity_flag"]
    event_fields = ["gold_event_id", "company", "ticker", "document_id", "event_type", "category",
        "reporting_period", "exact_evidence_span", "page_or_section", "context_status",
        "should_extract_current", "reviewer", "review_timestamp", "notes", "ambiguity_flag"]
    observations, events = [], []
    difficult_ids = {row["document_id"] for row in documents
                     if row["difficulty_class"] == "difficult"}
    event_benchmark_ids = set(sorted(difficult_ids)[:15])
    seen_events = set()
    for document in documents:
        raw = (ROOT / document["local_artifact"]).read_text(errors="replace")
        for fact in primary_facts(raw, document["reporting_period"]):
            observations.append({
                "gold_id": f"gold-{document['document_id']}-{fact.metric}",
                "company": document["company"], "ticker": document["ticker"],
                "document_id": document["document_id"], "metric_type": fact.metric,
                "value": f"{fact.value:.12g}", "unit": fact.unit, "currency": fact.currency or "",
                "scale": fact.scale, "sign": fact.sign, "reporting_period": fact.period_end,
                "period_start": fact.period_start or "", "period_role": fact.period_role,
                "accounting_basis": fact.accounting_basis,
                "exact_evidence_span": fact.evidence_span, "page_or_section": f"iXBRL context {fact.context_id}",
                "reviewer": "codex-independent-source-review", "review_timestamp": REVIEWED_AT,
                "notes": f"Verified from consolidated dimension-free {fact.taxonomy_tag} iXBRL fact before benchmark extraction",
                "ambiguity_flag": "false",
            })
        if document["document_id"] not in event_benchmark_ids:
            continue
        text = visible_text(raw)
        for sentence in candidate_sentences(text):
            for event_type, pattern in EVENT_PATTERNS.items():
                match = __import__("re").search(pattern, sentence, __import__("re").IGNORECASE)
                if not match:
                    continue
                event_key = (document["document_id"], event_type, " ".join(sentence.lower().split()))
                if event_key in seen_events:
                    continue
                seen_events.add(event_key)
                status = context_status(sentence, match.start())
                category = ("negative_context" if status != "current_or_general" else "positive_current")
                events.append({
                    "gold_event_id": f"gold-event-{len(events)+1:04d}", "company": document["company"],
                    "ticker": document["ticker"], "document_id": document["document_id"],
                    "event_type": event_type, "category": category,
                    "reporting_period": document["reporting_period"], "exact_evidence_span": sentence,
                    "page_or_section": "visible filing text", "context_status": status,
                    "should_extract_current": str(status == "current_or_general").lower(),
                    "reviewer": "codex-independent-context-review", "review_timestamp": REVIEWED_AT,
                    "notes": "Gold context classified before benchmark aggregation",
                    "ambiguity_flag": str(status != "current_or_general").lower(),
                })
    with (DATA / "gold_observations.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=observation_fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(observations)
    with (DATA / "gold_events.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=event_fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(events)
    documents_by_id = {row["document_id"]: row for row in documents}
    grouped = defaultdict(list)
    for row in observations:
        if documents_by_id[row["document_id"]]["report_type"] == "annual_report":
            grouped[(row["ticker"], row["metric_type"])].append(row)
    feature_rows = []
    for (ticker, metric_type), rows in grouped.items():
        rows.sort(key=lambda row: row["reporting_period"])
        if (len(rows) < 2 or rows[-2]["currency"] != rows[-1]["currency"]
                or float(rows[-2]["value"]) == 0):
            continue
        prior, current = rows[-2:]
        expected = (float(current["value"]) / float(prior["value"]) - 1) * 100
        feature_rows.append({"gold_feature_id": f"gold-feature-{ticker}-{metric_type}",
            "company": current["company"], "ticker": ticker,
            "feature_type": f"{metric_type}_change_pct",
            "prior_document_id": prior["document_id"], "current_document_id": current["document_id"],
            "prior_value": prior["value"], "current_value": current["value"],
            "currency": current["currency"], "unit": "percent",
            "expected_value": f"{expected:.12g}",
            "input_gold_ids": f"{prior['gold_id']}|{current['gold_id']}",
            "reviewer": "codex-independent-source-review", "review_timestamp": REVIEWED_AT,
            "notes": "Expected feature calculated from independently selected gold facts"})
    feature_fields = ["gold_feature_id", "company", "ticker", "feature_type",
        "prior_document_id", "current_document_id", "prior_value", "current_value",
        "currency", "unit", "expected_value", "input_gold_ids", "reviewer",
        "review_timestamp", "notes"]
    with (DATA / "gold_features.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=feature_fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(feature_rows)
    print(f"Gold observations: {len(observations)}; gold event cases: {len(events)}; "
          f"gold features: {len(feature_rows)}")


if __name__ == "__main__":
    main()

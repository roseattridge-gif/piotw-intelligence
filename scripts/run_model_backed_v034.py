from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_1.guard import verify_frozen_isolation
from evidence_engine_v0_2.ixbrl import visible_text
from evidence_engine_v0_3.ai_finops import compare_events, count_classes, validate_import
from evidence_engine_v0_3_3.events import attribute_subject
from evidence_engine_v0_3_4.events import extract_contextual_events_v034, extract_event_pipeline
from evidence_engine_v0_3_4.semantic import (
    DeterministicSemanticVerifier,
    OpenAIResponsesSemanticVerifier,
    SemanticCandidate,
    SemanticDecisionCache,
)

MODEL = "gpt-5-mini"
PROMPT_VERSION = "semantic-event-v0.3.4"
SCHEMA_VERSION = "semantic-schema-v0.3.4"
BATCH_TRANSPORT_VERSION = "semantic-batch-v0.3.4.1"
BATCH_SCHEMA_VERSION = "semantic-batch-schema-v0.3.4.1"
BATCH_SIZE = 20
INPUT_PRICE_PER_M = 0.25
OUTPUT_PRICE_PER_M = 2.0
NEW_TICKERS = {"MMM", "INTC", "MSFT"}
GM_TICKERS = {"GM", "HON", "HPQ"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RecordingVerifier:
    provider = "openai"
    model_version = MODEL
    prompt_version = PROMPT_VERSION
    max_output_tokens = 16000

    def __init__(self, api_key: str, output: Path):
        self.delegate = OpenAIResponsesSemanticVerifier(api_key, model=MODEL,
            max_output_tokens=1500, batch_size=BATCH_SIZE, batch_max_output_tokens=16000)
        self.output = output
        self.prefilled: dict[str, object] = {}
        self.last_batch_records: list[dict] = []
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("")

    def verify(self, candidate: SemanticCandidate):
        decision = self.delegate.verify(candidate)
        record = dict(self.delegate.last_call_record or {})
        record["candidate_id"] = hashlib.sha256(
            f"{candidate.target_company}|{candidate.candidate_event_type}|{candidate.exact_candidate_span}".encode()
        ).hexdigest()[:20]
        record["target_company"] = candidate.target_company
        record["candidate_event_type"] = candidate.candidate_event_type
        record["estimated_cost_usd"] = (
            decision.input_tokens * INPUT_PRICE_PER_M + decision.output_tokens * OUTPUT_PRICE_PER_M
        ) / 1_000_000
        with self.output.open("a") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        return decision

    def verify_many(self, candidates: list[SemanticCandidate]):
        keys = [self.candidate_key(candidate) for candidate in candidates]
        missing = [candidate for key, candidate in zip(keys, candidates, strict=True)
            if key not in self.prefilled]
        if missing:
            new_decisions = self.delegate.verify_many(missing)
            for candidate, decision in zip(missing, new_decisions, strict=True):
                self.prefilled[self.candidate_key(candidate)] = decision
        else:
            self.delegate.last_batch_records = []
        self.last_batch_records = list(self.delegate.last_batch_records)
        for record in self.last_batch_records:
            record = dict(record)
            record["estimated_cost_usd"] = (
                record.get("input_tokens", 0) * INPUT_PRICE_PER_M
                + record.get("output_tokens", 0) * OUTPUT_PRICE_PER_M
            ) / 1_000_000
            with self.output.open("a") as handle:
                handle.write(json.dumps(record, sort_keys=True) + "\n")
        return [self.prefilled[key] for key in keys]

    @staticmethod
    def candidate_key(candidate: SemanticCandidate) -> str:
        return hashlib.sha256(json.dumps(asdict(candidate), sort_keys=True).encode()).hexdigest()

    def prefill(self, candidates: list[SemanticCandidate]) -> None:
        unique = {self.candidate_key(candidate): candidate for candidate in candidates}
        self.verify_many(list(unique.values()))


class CollectingVerifier:
    provider = "candidate_collection_only"
    model_version = MODEL
    prompt_version = PROMPT_VERSION

    def __init__(self):
        self.candidates: list[SemanticCandidate] = []
        self.delegate = DeterministicSemanticVerifier()
        self.last_batch_records: list[dict] = []

    def verify_many(self, candidates: list[SemanticCandidate]):
        self.candidates.extend(candidates)
        self.last_batch_records = []
        return [self.delegate.verify(candidate) for candidate in candidates]

    def verify(self, candidate: SemanticCandidate):
        self.candidates.append(candidate)
        return self.delegate.verify(candidate)


def run_documents(rows: list[dict], artifact_field: str, verifier,
                  cache: SemanticDecisionCache | None) -> tuple[Counter, list[dict]]:
    totals: Counter = Counter(); accepted: list[dict] = []
    for row in rows:
        text = visible_text((ROOT / row[artifact_field]).read_text(errors="ignore"))
        pipeline = extract_event_pipeline(text, target_company=row["company"],
            publication_date=row["publication_date"], reporting_period=row["reporting_period"],
            verifier=verifier, cache=cache)
        totals.update({"documents": 1, "candidates": len(pipeline["candidates"]),
            "deterministic_rejects": len(pipeline["event_rejections"]) - len(pipeline["semantic_rejections"]),
            "semantic_calls": pipeline["semantic_calls"], "cache_hits": pipeline["semantic_cache_hits"],
            "accepted": len(pipeline["accepted_events"]), "rejected": len(pipeline["semantic_rejections"]),
            "ambiguous": len(pipeline["semantic_ambiguous"])})
        for event in pipeline["accepted_events"]:
            accepted.append({"document_id": row["document_id"], "company": row["company"],
                "event_type": event["event_type"], "source_span": event["source_span"],
                "support_span": event["semantic_exact_support_span"],
                "subject_type": event["semantic_subject_type"],
                "reason_code": event["semantic_reason_code"]})
    return totals, accepted


def label_summary(accepted: list[dict], labelled_path: Path, *, classification_field: str) -> dict:
    accepted_by_key = {(row["document_id"], row["event_type"], row["source_span"]): row
        for row in accepted}
    labelled = list(csv.DictReader(labelled_path.open()))
    accepted_labels = [{**row, "support_span": accepted_by_key[key]["support_span"]}
        for row in labelled
        if (key := (row["document_id"], row["event_type"], row["source_span"]))
        in accepted_by_key]
    counts = Counter(row[classification_field] for row in accepted_labels)
    supported_total = sum(row[classification_field] == "supported" for row in labelled)
    false_positive_total = sum(row[classification_field] == "false_positive" for row in labelled)
    denominator = counts["supported"] + counts["false_positive"]
    return {"inspected": len(labelled), "accepted_inspected": len(accepted_labels),
        "supported": counts["supported"], "false_positives": counts["false_positive"],
        "ambiguous_labels_accepted": counts["ambiguous"],
        "precision": counts["supported"] / denominator if denominator else None,
        "supported_retained": counts["supported"], "supported_total": supported_total,
        "supported_retention": counts["supported"] / max(supported_total, 1),
        "false_positive_total": false_positive_total,
        "severe_false_positives": sum(row.get("severe") == "true" and row[classification_field] == "false_positive"
                                      for row in accepted_labels),
        "attribution_errors": sum(row.get("failure_class") in {"third_party_attribution", "supplier_attribution",
            "customer_attribution", "competitor_attribution", "industry_context"}
            and row[classification_field] == "false_positive" for row in accepted_labels),
        "provenance_completeness": sum(bool(row["support_span"] and row["support_span"] in row["source_span"])
                                       for row in accepted_labels) / max(len(accepted_labels), 1)}


def benchmark_run(verifier: RecordingVerifier) -> dict:
    rows = list(csv.DictReader((ROOT / "data/evidence_engine_v0_3_4/semantic_event_benchmark.csv").open()))
    decisions = Counter(); correct = 0; accepted_supported = 0; supported_total = 0
    candidates = []
    for row in rows:
        subject = attribute_subject(row["source_context"])
        candidates.append(SemanticCandidate(target_company=row.get("company") or "target company",
            candidate_event_type=row["candidate_event_type"], exact_candidate_span=row["source_context"],
            context=row["source_context"], heading=None, publication_date=None,
            deterministic_metadata={"subject_type": subject.subject_type,
                "entity_scope": subject.entity_scope, "factual_status": subject.status,
                "event_status": "current", "allowed_remaps": []}))
    batch_decisions = verifier.verify_many(candidates)
    for row, decision in zip(rows, batch_decisions, strict=True):
        decisions[decision.decision] += 1
        correct += decision.decision == row["expected_decision"]
        supported_total += row["expected_decision"] == "accept"
        accepted_supported += row["expected_decision"] == "accept" and decision.decision == "accept"
    return {"cases": len(rows), **dict(decisions), "decision_accuracy": correct / max(len(rows), 1),
        "supported_retained": accepted_supported, "supported_total": supported_total,
        "supported_retention": accepted_supported / max(supported_total, 1)}


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or api_key == "PASTE_KEY_HERE":
        raise SystemExit("MODEL_BACKED_VERIFICATION_BLOCKED_NO_CREDENTIAL")
    protected_before = verify_frozen_isolation(ROOT)
    started = datetime.now(UTC)
    audit_path = ROOT / "data/derived/evidence_engine_v0_3_4_1_semantic_batch_calls.jsonl"
    cache = SemanticDecisionCache(ROOT / "data/derived/evidence_engine_v0_3_4_1_openai_batch_cache.json")
    verifier = RecordingVerifier(api_key, audit_path)
    imported = validate_import(ROOT)
    manifest_v3 = imported["corpus"]
    manifest_v2 = list(csv.DictReader((ROOT / "data/evidence_engine_v0_2/corpus_manifest.csv").open()))
    prior_ids = {row["document_id"] for row in csv.DictReader(
        (ROOT / "data/evidence_engine_v0_3_2/second_unseen_inspected_events.csv").open())}
    prior_rows = [row for row in manifest_v3 if row["document_id"] in prior_ids]
    gm_rows = [row for row in manifest_v2 if row["ticker"] in GM_TICKERS]
    unseen_rows = [row for row in manifest_v2 if row["ticker"] in NEW_TICKERS]

    collector = CollectingVerifier()
    benchmark_run(collector)
    collecting_extractor = lambda text, **kwargs: extract_contextual_events_v034(
        text, verifier=collector, cache=None, **kwargs)
    compare_events(ROOT, imported, extractor=collecting_extractor)
    run_documents(prior_rows, "source_artifact", collector, None)
    run_documents(gm_rows, "local_artifact", collector, None)
    run_documents(unseen_rows, "local_artifact", collector, None)
    verifier.prefill(collector.candidates)

    benchmark = benchmark_run(verifier)
    extractor = lambda text, **kwargs: extract_contextual_events_v034(
        text, verifier=verifier, cache=cache, **kwargs)
    six = compare_events(ROOT, imported, extractor=extractor)
    six_classes = Counter(row["classification"] for row in six)

    prior_totals, prior_accepted = run_documents(prior_rows, "source_artifact", verifier, cache)
    prior = {**dict(prior_totals), **label_summary(prior_accepted,
        ROOT / "data/evidence_engine_v0_3_2/second_unseen_inspected_events.csv",
        classification_field="manual_sanity_classification")}

    gm_totals, gm_accepted = run_documents(gm_rows, "local_artifact", verifier, cache)
    gm = {**dict(gm_totals), **label_summary(gm_accepted,
        ROOT / "data/evidence_engine_v0_3_3/new_unseen_inspected_events.csv",
        classification_field="manual_sanity_classification")}

    unseen_totals, unseen_accepted = run_documents(unseen_rows, "local_artifact", verifier, cache)
    unseen = {**dict(unseen_totals), **label_summary(unseen_accepted,
        ROOT / "data/evidence_engine_v0_3_4/new_unseen_semantic_inspection.csv",
        classification_field="diagnostic_classification")}

    calls = [json.loads(line) for line in audit_path.read_text().splitlines() if line]
    input_tokens = sum(row.get("input_tokens", 0) for row in calls)
    output_tokens = sum(row.get("output_tokens", 0) for row in calls)
    total_cost = sum(row.get("estimated_cost_usd", 0) for row in calls)
    latency = sum(row.get("latency_ms", 0) for row in calls)
    reports = prior_totals["documents"] + gm_totals["documents"] + unseen_totals["documents"] + 6
    gate_passed = bool(unseen["precision"] is not None and unseen["precision"] >= .85
        and unseen["severe_false_positives"] == 0 and unseen["attribution_errors"] == 0
        and unseen["supported_retention"] >= .85 and unseen["provenance_completeness"] == 1
        and six_classes["PIOTW_MISSED_EVENT"] == 0
        and six_classes["PIOTW_FALSE_POSITIVE"] == 0
        and benchmark["supported_retention"] >= .85)
    results = {"version": "0.3.4", "authorised_calls_ran": bool(calls),
        "provider": "openai", "model": MODEL, "model_snapshot": None,
        "prompt_version": PROMPT_VERSION, "schema_version": SCHEMA_VERSION,
        "batch_transport_version": BATCH_TRANSPORT_VERSION,
        "batch_schema_version": BATCH_SCHEMA_VERSION, "batch_size": BATCH_SIZE,
        "temperature": None, "max_output_tokens": 16000,
        "run_started_at": started.isoformat(), "run_completed_at": datetime.now(UTC).isoformat(),
        "benchmark": benchmark,
        "six_document_ai_diagnostic": {"classifications": count_classes(six),
            "missed_ai_events": six_classes["PIOTW_MISSED_EVENT"],
            "likely_false_positives": six_classes["PIOTW_FALSE_POSITIVE"],
            "duplicates": six_classes["DUPLICATE_EVENT"]},
        "previous_unseen": prior, "gm_honeywell_hp": gm, "brand_new_unseen": unseen,
        "live_costs": {"calls": len(calls), "input_tokens": input_tokens,
            "output_tokens": output_tokens, "total_tokens": input_tokens + output_tokens,
            "total_cost_usd": total_cost, "cost_per_call_usd": total_cost / max(len(calls), 1),
            "cost_per_report_usd": total_cost / max(reports, 1),
            "average_latency_ms_per_call": latency / max(len(calls), 1),
            "average_latency_ms_per_report": latency / max(reports, 1)},
        "gate": {"passed": gate_passed,
            "technical_status": "TECHNICALLY READY FOR BLINDED CROSS-REVIEW" if gate_passed else "NOT TECHNICALLY READY"},
        "extractor_frozen": False, "cross_review_pack_created": False,
        "official_model2_readiness": "NOT READY", "outcomes_accessed": False,
        "model2_trained": False, "protected_artifacts": len(verify_frozen_isolation(ROOT)),
        "hashes": {"prompt": sha(ROOT / "config/evidence/semantic_event_prompt_v0_3_4.txt"),
            "batch_transport_prompt": sha(ROOT / "config/evidence/semantic_batch_transport_v0_3_4_1.txt"),
            "schema_provider": sha(ROOT / "evidence_engine_v0_3_4/semantic.py"),
            "decision_logic": sha(ROOT / "evidence_engine_v0_3_4/events.py"),
            "taxonomy": sha(ROOT / "config/evidence/event_taxonomy_v0_1.yaml"),
            "config": sha(ROOT / "config/evidence/semantic_verifier_v0_3_4_1.yaml")}}
    if protected_before != verify_frozen_isolation(ROOT):
        raise RuntimeError("protected artefacts changed")
    (ROOT / "data/derived/evidence_engine_v0_3_4_1_model_backed_batched_results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": results["gate"]["technical_status"],
        "calls": len(calls), "gate_passed": gate_passed}))


if __name__ == "__main__":
    main()

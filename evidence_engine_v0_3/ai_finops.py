from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from evidence_engine_v0_2.events import extract_contextual_events
from evidence_engine_v0_2.ixbrl import primary_facts, visible_text

REVIEWER_TYPE = "AI_ASSISTED_FINOPS_FIRST_PASS"
REVIEWER_IDENTITY = "OpenAI GPT-5.6 Sol"
STATUS = "exploratory_diagnostic"
METRIC_ALIASES = {"adjusted_EBITDA": "adjusted_ebitda"}
EVENT_ALIASES = {
    "growth": "growth_language",
    "investment": "major_investment",
    "margin_pressure": "margin_deterioration",
    "recovery": "recovery_language",
}
SEVERE_NUMERIC = {
    "wrong_sign", "wrong_period", "wrong_scale", "wrong_currency",
    "adjusted_statutory_confusion", "net_debt_net_cash_reversal",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def validate_import(root: Path) -> dict:
    base = root / "data/ai_finops_first_pass/original"
    numerical = rows(base / "piotw_ai_finops_first_pass_numerical.csv")
    events = rows(base / "piotw_ai_finops_first_pass_events.csv")
    corpus = rows(root / "data/evidence_engine_v0_3/corpus_manifest.csv")
    known = {row["document_id"] for row in corpus}
    expected_num = {"document_id", "metric_type", "value", "unit", "scale", "currency", "period",
                    "accounting_basis", "source_page_section", "exact_evidence_span", "reviewer_id",
                    "annotation_timestamp", "ambiguity_flag", "notes"}
    expected_event = {"document_id", "reviewer_free_text_label", "mapped_event_type", "label_status",
                      "source_page_section", "exact_evidence_span", "reviewer_id", "annotation_timestamp",
                      "ambiguity_flag", "notes"}
    if set(numerical[0]) != expected_num or set(events[0]) != expected_event:
        raise ValueError("AI reviewer schema is not compatible")
    for row in numerical + events:
        if row["document_id"] not in known:
            raise ValueError(f"unknown document id: {row['document_id']}")
        if row["reviewer_id"] != "openai-gpt-5.6-sol-finops-first-pass":
            raise ValueError("unexpected reviewer identity")
        datetime.fromisoformat(row["annotation_timestamp"])
        if not row["source_page_section"] or not row["exact_evidence_span"]:
            raise ValueError("source page and evidence span are required")
        if row["ambiguity_flag"] not in {"yes", "no"}:
            raise ValueError("invalid ambiguity flag")
    return {"numerical": numerical, "events": events, "corpus": corpus}


def _period_matches(ai_period: str, end: str) -> bool:
    if end in ai_period:
        return True
    year = end[:4]
    return ai_period.lower() in {f"fy{year}", year}


def _token_similarity(left: str, right: str) -> float:
    stop = {"the", "and", "for", "with", "that", "from", "were", "was", "are", "our", "its"}
    a = {token for token in re.findall(r"[a-z]{3,}", left.lower()) if token not in stop}
    b = {token for token in re.findall(r"[a-z]{3,}", right.lower()) if token not in stop}
    return len(a & b) / len(a | b) if a | b else 0.0


def compare_numerical(root: Path, imported: dict) -> list[dict]:
    manifest = {row["document_id"]: row for row in imported["corpus"]}
    reviewed_ids = {row["document_id"] for row in imported["numerical"]} | {
        row["document_id"] for row in imported["events"]}
    engine: dict[str, list[dict]] = {}
    for document_id in reviewed_ids:
        row = manifest[document_id]
        document = (root / row["source_artifact"]).read_text(errors="ignore")
        engine[document_id] = [asdict(fact) for fact in primary_facts(document, row["reporting_period"])]
    output = []
    matched = set()
    for index, original in enumerate(imported["numerical"], 1):
        normalized_metric = METRIC_ALIASES.get(original["metric_type"], original["metric_type"].lower())
        candidates = [(i, fact) for i, fact in enumerate(engine[original["document_id"]])
                      if fact["metric"] == normalized_metric]
        base = {
            "comparison_id": f"num-{index:03d}", "document_id": original["document_id"],
            "ai_original_metric": original["metric_type"], "ai_normalized_metric": normalized_metric,
            "ai_original_value": original["value"], "ai_original_unit": original["unit"],
            "ai_original_scale": original["scale"], "ai_original_currency": original["currency"],
            "ai_original_period": original["period"], "ai_original_accounting_basis": original["accounting_basis"],
            "ai_source_page_section": original["source_page_section"],
            "ai_exact_evidence_span": original["exact_evidence_span"],
            "ai_ambiguity_flag": original["ambiguity_flag"],
        }
        if not candidates:
            output.append(base | {"classification": "PIOTW_MISSING", "piotw_metric": "",
                "piotw_value_million": "", "piotw_period_end": "", "piotw_accounting_basis": "",
                "field_disagreements": "metric_not_extracted", "severe": "false",
                "root_cause": "PIOTW parser coverage gap", "diagnosis": "AI metric is outside current deterministic tag coverage."})
            continue
        candidate_index, fact = max(candidates, key=lambda item: int(_period_matches(original["period"], item[1]["period_end"])))
        matched.add((original["document_id"], candidate_index))
        ai_million = float(original["value"]) * int(original["scale"]) / 1_000_000
        disagreements = []
        if abs(ai_million - fact["value"]) > 1e-6:
            disagreements.append("wrong_sign" if abs(ai_million) == abs(fact["value"]) else "value")
        if original["currency"] != (fact["currency"] or ""):
            disagreements.append("wrong_currency")
        if int(original["scale"]) != 10 ** int(fact["scale"]):
            disagreements.append("wrong_scale")
        if not _period_matches(original["period"], fact["period_end"]):
            disagreements.append("wrong_period")
        if original["accounting_basis"] != fact["accounting_basis"]:
            disagreement = "adjusted_statutory_confusion" if {
                original["accounting_basis"], fact["accounting_basis"]
            } == {"adjusted", "statutory"} else "accounting_basis"
            disagreements.append(disagreement)
        evidence_similarity = _token_similarity(original["exact_evidence_span"], fact["evidence_span"])
        severe = bool(SEVERE_NUMERIC & set(disagreements))
        if original["ambiguity_flag"] == "yes":
            classification = "AMBIGUOUS"
        elif "wrong_period" in disagreements:
            classification = "PERIOD_DISAGREEMENT"
        elif {"adjusted_statutory_confusion", "accounting_basis"} & set(disagreements):
            classification = "ACCOUNTING_BASIS_DISAGREEMENT"
        elif {"wrong_currency", "wrong_scale"} & set(disagreements):
            classification = "UNIT_SCALE_CURRENCY_DISAGREEMENT"
        elif disagreements:
            classification = "VALUE_DISAGREEMENT"
        elif evidence_similarity >= 0.15:
            classification = "EXACT_AGREEMENT"
        else:
            classification = "SEMANTIC_AGREEMENT"
        diagnosis = "Factual fields agree; PIOTW uses tagged iXBRL provenance rather than the visual table citation."
        root_cause = "equivalent source representations"
        if disagreements == ["wrong_sign"] and normalized_metric == "capex":
            diagnosis = "Reviewer records cash-flow presentation sign; PIOTW records the positive expenditure magnitude from the iXBRL fact."
            root_cause = "metric-definition mismatch"
        elif "accounting_basis" in disagreements:
            diagnosis = "Reviewer selected a rounded narrative/company-defined capex figure; PIOTW selected the exact statutory iXBRL cash-flow fact."
            root_cause = "metric-definition mismatch"
        output.append(base | {"classification": classification, "piotw_metric": fact["metric"],
            "piotw_value_million": fact["value"], "piotw_period_end": fact["period_end"],
            "piotw_accounting_basis": fact["accounting_basis"],
            "piotw_evidence_span": fact["evidence_span"],
            "provenance_similarity": round(evidence_similarity, 4),
            "field_disagreements": "|".join(disagreements), "severe": str(severe).lower(),
            "root_cause": root_cause, "diagnosis": diagnosis})
    counter = len(output)
    for document_id, facts in engine.items():
        for index, fact in enumerate(facts):
            if (document_id, index) in matched:
                continue
            counter += 1
            output.append({"comparison_id": f"num-{counter:03d}", "document_id": document_id,
                "ai_original_metric": "", "ai_normalized_metric": "", "ai_original_value": "",
                "ai_original_unit": "", "ai_original_scale": "", "ai_original_currency": "",
                "ai_original_period": "", "ai_original_accounting_basis": "",
                "ai_source_page_section": "", "ai_exact_evidence_span": "", "ai_ambiguity_flag": "",
                "classification": "AI_REVIEW_MISSING", "piotw_metric": fact["metric"],
                "piotw_value_million": fact["value"], "piotw_period_end": fact["period_end"],
                "piotw_accounting_basis": fact["accounting_basis"], "piotw_evidence_span": fact["evidence_span"],
                "provenance_similarity": "", "field_disagreements": "reviewer_selective_omission",
                "severe": "false", "root_cause": "AI reviewer omission",
                "diagnosis": "PIOTW extracted an in-scope fact that the deliberately selective first pass did not annotate."})
    return output


def _likely_false_positive(event: dict) -> bool:
    if event.get("context_status") in {"current", "ongoing", "planned"}:
        return False
    text = event["evidence_span"].lower()
    return any(token in text for token in (
        " may ", " could ", " if ", "risk", "career", "served as", "redundancy and other continuity",
        "as a simplification", "assumptions about", "deemed to be significant assumptions"))


def compare_events(root: Path, imported: dict, *, extractor=None) -> list[dict]:
    manifest = {row["document_id"]: row for row in imported["corpus"]}
    reviewed_ids = {row["document_id"] for row in imported["events"]} | {
        row["document_id"] for row in imported["numerical"]}
    engine = {}
    for document_id in reviewed_ids:
        row = manifest[document_id]
        document = (root / row["source_artifact"]).read_text(errors="ignore")
        engine[document_id] = (extractor(visible_text(document),
            publication_date=row["publication_date"], reporting_period=row["reporting_period"])
            if extractor else extract_contextual_events(visible_text(document)))
    output = []
    matched = set()
    for index, original in enumerate(imported["events"], 1):
        normalized = EVENT_ALIASES.get(original["mapped_event_type"], original["mapped_event_type"])
        candidates = []
        for i, event in enumerate(engine[original["document_id"]]):
            same_type = event["event_type"] == normalized
            similarity = _token_similarity(original["exact_evidence_span"], event["evidence_span"])
            if same_type:
                candidates.append((similarity, i, event))
        base = {"comparison_id": f"event-{index:03d}", "document_id": original["document_id"],
            "ai_original_event_type": original["mapped_event_type"], "ai_normalized_event_type": normalized,
            "ai_label_status": original["label_status"], "ai_source_page_section": original["source_page_section"],
            "ai_exact_evidence_span": original["exact_evidence_span"],
            "ai_ambiguity_flag": original["ambiguity_flag"]}
        if original["label_status"] == "ambiguous" and not original["mapped_event_type"]:
            output.append(base | {"classification": "AMBIGUOUS", "piotw_event_type": "",
                "piotw_evidence_span": "", "evidence_similarity": "", "severe": "false",
                "root_cause": "incomplete reviewer PDF", "diagnosis": "Source-pack completeness issue; not an event comparison."})
            continue
        if not candidates:
            severe = normalized in {"redundancy", "cost_reduction", "liquidity_concern", "operational_disruption"}
            output.append(base | {"classification": "PIOTW_MISSED_EVENT", "piotw_event_type": "",
                "piotw_evidence_span": "", "evidence_similarity": "", "severe": str(severe).lower(),
                "root_cause": "PIOTW context/taxonomy error" if normalized not in EVENT_ALIASES.values() else "taxonomy coverage gap",
                "diagnosis": "The deterministic event patterns did not identify this independently described condition."})
            continue
        similarity, candidate_index, event = max(candidates)
        if similarity >= 0.15:
            matched.add((original["document_id"], candidate_index))
            classification = "EVENT_AGREEMENT"
            diagnosis = "Same event type and substantively overlapping evidence."
        else:
            classification = "PIOTW_MISSED_EVENT"
            diagnosis = "PIOTW found a different occurrence with the same taxonomy label, but missed this cited event."
        output.append(base | {"classification": classification, "piotw_event_type": event["event_type"],
            "piotw_evidence_span": event["evidence_span"], "evidence_similarity": round(similarity, 4),
            "severe": "false", "root_cause": "equivalent event evidence" if similarity >= 0.15 else "duplicate evidence or broad taxonomy",
            "diagnosis": diagnosis})
    counter = len(output)
    piotw_only_seen: list[tuple[str, str, str]] = []
    for document_id, events in engine.items():
        for index, event in enumerate(events):
            if (document_id, index) in matched:
                continue
            counter += 1
            false_positive = _likely_false_positive(event)
            duplicate = any(
                prior_document == document_id and prior_type == event["event_type"]
                and _token_similarity(prior_span, event["evidence_span"]) >= 0.85
                for prior_document, prior_type, prior_span in piotw_only_seen
            )
            piotw_only_seen.append((document_id, event["event_type"], event["evidence_span"]))
            classification = "DUPLICATE_EVENT" if duplicate else (
                "PIOTW_FALSE_POSITIVE" if false_positive else "AI_REVIEW_MISSING"
            )
            output.append({"comparison_id": f"event-{counter:03d}", "document_id": document_id,
                "ai_original_event_type": "", "ai_normalized_event_type": "", "ai_label_status": "",
                "ai_source_page_section": "", "ai_exact_evidence_span": "", "ai_ambiguity_flag": "",
                "classification": classification,
                "piotw_event_type": event["event_type"], "piotw_evidence_span": event["evidence_span"],
                "evidence_similarity": "", "severe": str((false_positive or duplicate) and event["event_type"] in {"restructuring", "redundancy", "site_closure"}).lower(),
                "root_cause": "duplicate evidence" if duplicate else "PIOTW context/taxonomy error" if false_positive else "AI reviewer omission",
                "diagnosis": "Near-duplicate occurrence would inflate the same event feature." if duplicate else "Keyword hit is hypothetical, biographical, or semantically unrelated." if false_positive else "Plausible extracted event omitted from a deliberately selective AI pass; human adjudication required."})
    return output


def count_classes(comparisons: list[dict]) -> dict:
    counts = Counter(row["classification"] for row in comparisons)
    return {key: {"count": value, "total": len(comparisons), "rate": value / len(comparisons) if comparisons else None}
            for key, value in sorted(counts.items())}


def write_csv(path: Path, comparisons: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(comparisons[0])
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader(); writer.writerows(comparisons)


def run(root: Path) -> dict:
    imported = validate_import(root)
    numerical = compare_numerical(root, imported)
    events = compare_events(root, imported)
    derived = root / "data/derived"
    write_csv(derived / "evidence_engine_v0_3_ai_finops_numerical_comparison.csv", numerical)
    write_csv(derived / "evidence_engine_v0_3_ai_finops_event_comparison.csv", events)
    manifest = {row["document_id"]: row for row in imported["corpus"]}
    document_ids = sorted({row["document_id"] for row in imported["numerical"] + imported["events"]})
    gold_freeze = json.loads((root / "data/evidence_engine_v0_3/annotation_freeze_manifest.json").read_text())
    formal_gold_unchanged = all(
        sha256(root / "data/evidence_engine_v0_3" / name) == digest
        for name, digest in gold_freeze["blank_file_hashes"].items()
        if name in {"gold_observations.csv", "gold_events.csv"}
    )
    metadata = {
        "namespace": "ai_finops_first_pass", "reviewer_type": REVIEWER_TYPE,
        "reviewer_identity": REVIEWER_IDENTITY, "status": STATUS, "formal_gold": False,
        "admissible_for_model2_gate": False,
        "formal_human_gold_unchanged": formal_gold_unchanged,
        "source_drive_folder": "https://drive.google.com/drive/folders/1_uv_LDU5E1AndGuBBOWLb5piP5MVmfnQ",
        "source_files": {path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
                         for path in sorted((root / "data/ai_finops_first_pass/original").iterdir())},
    }
    (root / "data/ai_finops_first_pass/import_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    source_issue = {
        "issue_id": "EE03-SOURCE-001", "document_id": "ee03-alb-0000915913-24-000156",
        "classification": "review_pack_source_completeness_defect", "confirmed": True,
        "primary_html_contains_exhibit_link": True, "reviewer_pdf_contains_exhibit_body": False,
        "piotw_primary_document_numeric_facts": 0, "comparison_methodologically_fair": False,
        "evidence": "Primary HTML links to a3q24earningsreleaseex991.htm; reviewer PDF renders only the 8-K wrapper.",
        "recommended_action": "Issue a versioned corrected blinded pack before formal human review; preserve the original pack.",
    }
    (root / "data/ai_finops_first_pass/source_pack_issues.json").write_text(json.dumps([source_issue], indent=2) + "\n")
    results = {
        "methodological_boundary": "AI-assisted reviewer diagnostic agreement; not independent extraction accuracy",
        "metadata": metadata, "official_readiness_status": "NOT READY",
        "outcomes_accessed": False, "model2_trained": False,
        "scope": {"companies": len({manifest[doc]["company"] for doc in document_ids}),
                  "documents": len(document_ids), "document_ids": document_ids,
                  "report_types": dict(Counter(manifest[doc]["report_type"] for doc in document_ids)),
                  "ai_numerical_annotations": len(imported["numerical"]),
                  "ai_event_annotations": len(imported["events"]),
                  "metric_names": sorted({row["metric_type"] for row in imported["numerical"]}),
                  "event_labels": sorted({row["mapped_event_type"] for row in imported["events"] if row["mapped_event_type"]})},
        "numerical": {"row_comparisons": len(numerical), "ai_reviewed_denominator": len(imported["numerical"]),
                      "classifications": count_classes(numerical),
                      "diagnostic_counts": {
                          "exact_agreement": sum(row["classification"] == "EXACT_AGREEMENT" for row in numerical),
                          "semantic_agreement": sum(row["classification"] == "SEMANTIC_AGREEMENT" for row in numerical),
                          "piotw_omissions": sum(row["classification"] == "PIOTW_MISSING" for row in numerical),
                          "ai_review_omission_candidates": sum(row["classification"] == "AI_REVIEW_MISSING" for row in numerical),
                          "metric_identity_disagreements": sum(row["classification"] == "METRIC_IDENTITY_DISAGREEMENT" for row in numerical),
                          "period_disagreements": sum(row["classification"] == "PERIOD_DISAGREEMENT" for row in numerical),
                          "accounting_basis_disagreements": sum(row["classification"] == "ACCOUNTING_BASIS_DISAGREEMENT" for row in numerical),
                          "unit_scale_currency_disagreements": sum(row["classification"] == "UNIT_SCALE_CURRENCY_DISAGREEMENT" for row in numerical),
                          "value_disagreements": sum(row["classification"] == "VALUE_DISAGREEMENT" for row in numerical),
                      },
                      "severe_disagreements": {"count": sum(row["severe"] == "true" for row in numerical), "total": len(numerical)}},
        "events": {"row_comparisons": len(events), "ai_reviewed_denominator": len(imported["events"]),
                   "classifications": count_classes(events),
                   "diagnostic_counts": {
                       "event_agreement": sum(row["classification"] == "EVENT_AGREEMENT" for row in events),
                       "piotw_missed_events": sum(row["classification"] == "PIOTW_MISSED_EVENT" for row in events),
                       "piotw_false_positives": sum(row["classification"] == "PIOTW_FALSE_POSITIVE" for row in events),
                       "duplicate_events": sum(row["classification"] == "DUPLICATE_EVENT" for row in events),
                       "ai_review_omission_candidates": sum(row["classification"] == "AI_REVIEW_MISSING" for row in events),
                       "taxonomy_disagreements": sum(row["classification"] == "TAXONOMY_DISAGREEMENT" for row in events),
                       "timing_context_disagreements": sum(row["classification"] == "TIMING_CONTEXT_DISAGREEMENT" for row in events),
                       "ambiguous": sum(row["classification"] == "AMBIGUOUS" for row in events),
                   },
                   "severe_disagreements": {"count": sum(row["severe"] == "true" for row in events), "total": len(events)}},
        "source_pack_issues": [source_issue],
    }
    (derived / "evidence_engine_v0_3_ai_finops_comparison.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    return results

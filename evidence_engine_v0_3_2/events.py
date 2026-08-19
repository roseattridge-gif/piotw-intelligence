from __future__ import annotations

import re
from dataclasses import dataclass

from evidence_engine_v0_3_1.events import extract_event_pipeline as extract_v031_pipeline

ACCOUNTING_EVENT_TYPES = {"restructuring", "redundancy", "site_closure", "transformation"}
CURRENT_PROMOTION = re.compile(
    r"\b(?:during (?:20\d{2}|the current (?:quarter|year|period)) we (?:initiated|announced|commenced)|"
    r"in the current (?:quarter|year|period) we (?:initiated|announced|commenced)|"
    r"we (?:initiated|announced|commenced|implemented)|the company (?:is implementing|announced)|"
    r"effective 20\d{2}|current programme includes|"
    r"(?:initiated|commenced|implemented) (?:a |the )?(?:restructuring|site closure|workforce reduction))\b",
    re.IGNORECASE,
)
HISTORICAL_CONTEXT = re.compile(
    r"\b(?:prior restructuring actions?|previously announced|completed in (?:a )?prior year|"
    r"historical restructuring|legacy programme|prior-year initiative|remaining costs associated with|"
    r"implementation of (?:a )?previously announced plan|in 20(?:0\d|1\d|2[0-3]) and 20\d{2})\b",
    re.IGNORECASE,
)
ACCOUNTING_ROW = re.compile(
    r"\b(?:restructuring (?:charges?|costs?|provisions?)|impairment charges?|employee separations?|"
    r"contract terminations?|long-lived asset impairments?|adjusted|gaap|segment profit|"
    r"corporate items and eliminations|effective tax rate|costs? related to (?:our )?restructuring)\b",
    re.IGNORECASE,
)
ACCOUNTING_NON_EVENT = re.compile(r"\btroubled debt restructur(?:ing|ings|e|ed)\b", re.IGNORECASE)
MONITOR_ONLY = re.compile(r"\b(?:continue to monitor|monitoring)\b", re.IGNORECASE)
CONDITIONAL_OFFSET = re.compile(r"\bif we are unable to (?:fully )?offset\b", re.IGNORECASE)
TABLE_MARKERS = re.compile(
    r"(?:\btable of contents\b|\(millions? of dollars\)|\bnine months ended\b|"
    r"\bthree months ended\b|\b% change\b|\b20\d{2}\s+20\d{2}\b)",
    re.IGNORECASE,
)
PAGE_CONTAMINATION = re.compile(r"^\s*\d{1,3}\s+table of contents\b", re.IGNORECASE)


@dataclass(frozen=True)
class EvidenceStructure:
    structure_type: str
    structure_quality: str
    period_binding: str
    table_title: str | None
    row_label: str | None
    column_heading: str | None
    cell_value: str | None


def _number_tokens(span: str) -> list[str]:
    return re.findall(r"(?<![A-Za-z])\(?[-+$£€]?\d[\d,.]*%?\)?", span)


def is_malformed_fragment(span: str) -> bool:
    words = re.findall(r"[A-Za-z]+", span)
    numbers = _number_tokens(span)
    unmatched = span.count("(") != span.count(")")
    repeated_header = len(re.findall(r"\b(?:adjusted|gaap|20\d{2}|table of contents)\b", span, re.IGNORECASE)) >= 5
    low_grammar = len(numbers) >= 5 and len(words) / max(len(numbers), 1) < 2.5
    return unmatched or repeated_header or low_grammar or bool(PAGE_CONTAMINATION.search(span))


def classify_evidence_structure(span: str, reporting_period: str | None = None) -> EvidenceStructure:
    malformed = is_malformed_fragment(span)
    table = bool(TABLE_MARKERS.search(span) or ACCOUNTING_ROW.search(span) and len(_number_tokens(span)) >= 2)
    if malformed:
        kind, quality = "malformed_unknown_fragment", "low"
    elif re.match(r"^\s*[•*-]", span):
        kind, quality = "list_bullet", "high"
    elif (table or re.match(r"^\s*\d+\s+", span)) and re.search(
        r"\b(?:represents|related to|primarily|included|consist)\b", span, re.IGNORECASE
    ):
        kind, quality = "table_footnote", "medium"
    elif table:
        kind, quality = "table_row", "medium"
    else:
        kind, quality = "narrative_sentence", "high"
    years = [int(year) for year in re.findall(r"\b(20\d{2})\b", span)]
    current_year = int(reporting_period[:4]) if reporting_period else None
    if current_year and current_year in years and any(year < current_year for year in years):
        period = "current_and_comparative"
    elif current_year and years and all(year < current_year for year in years):
        period = "comparative_period"
    elif current_year and years and all(year > current_year for year in years):
        period = "future_period"
    elif current_year and current_year in years:
        period = "current_period"
    else:
        period = "multi_year_history" if len(set(years)) > 1 else "explicit_single_period" if years else "unknown"
    row = ACCOUNTING_ROW.search(span)
    value = _number_tokens(span)[0] if _number_tokens(span) else None
    return EvidenceStructure(kind, quality, period, None, row.group(0) if row else None, None, value)


def _table_disposition(event: dict, reporting_period: str | None) -> tuple[str, str, str]:
    span = event["source_span"]
    structure = classify_evidence_structure(span, reporting_period)
    current_year = reporting_period[:4] if reporting_period else None
    years = re.findall(r"\b(20\d{2})\b", span)
    historical = bool(HISTORICAL_CONTEXT.search(span))
    comparative_only = bool(
        years and current_year and current_year not in years
        and max(map(int, years)) < int(current_year)
    )
    accounting_only = event["event_type"] in ACCOUNTING_EVENT_TYPES and bool(ACCOUNTING_ROW.search(span))
    promoted = bool(CURRENT_PROMOTION.search(span))
    if ACCOUNTING_NON_EVENT.search(span):
        return "rejected", "accounting_measure_only", "accounting_term_not_operational_event"
    if CONDITIONAL_OFFSET.search(span):
        return "rejected", "hypothetical", "conditional_cost_offset_not_cost_reduction_event"
    if MONITOR_ONLY.search(span) and not re.search(r"\b(?:experienced|caused|resulted|affected)\b", span, re.IGNORECASE):
        return "ambiguous", "ambiguous", "monitoring_statement_without_direct_occurrence"
    if years and current_year and min(map(int, years)) < int(current_year) < max(map(int, years)):
        return "rejected", "ambiguous", "mixed_period_table_fragment"
    if PAGE_CONTAMINATION.search(span) and len(span) > 400:
        return "rejected", "ambiguous", "page_header_joined_to_unrelated_text"
    if structure.structure_quality == "low" and len(span) > 600:
        return "rejected", "ambiguous", "malformed_table_fragment"
    if historical or comparative_only:
        return "rejected", "historical", "historical_or_comparative_disclosure"
    if structure.structure_quality == "low" and event["event_type"] in ACCOUNTING_EVENT_TYPES:
        return "rejected", "ambiguous", "malformed_table_fragment"
    if accounting_only and not promoted:
        return "rejected", "accounting_measure_only", "financial_observation_not_operational_event"
    if structure.structure_type.startswith("table") and event["event_type"] in ACCOUNTING_EVENT_TYPES and not promoted:
        return "ambiguous", "ambiguous", "table_period_or_operational_support_unclear"
    return "accepted", event["event_status"], "current_operational_support"


def extract_event_pipeline(
    text: str,
    *,
    publication_date: str | None = None,
    reporting_period: str | None = None,
    page_or_section: str | None = None,
) -> dict:
    base = extract_v031_pipeline(
        text,
        publication_date=publication_date,
        reporting_period=reporting_period,
        page_or_section=page_or_section,
    )
    candidates = []
    for candidate in base["candidates"]:
        structure = classify_evidence_structure(candidate["source_span"], reporting_period)
        candidates.append({**candidate, **structure.__dict__})
    accepted, table_rejections, table_ambiguous = [], [], []
    for event in base["accepted_events"]:
        structure = classify_evidence_structure(event["source_span"], reporting_period)
        decision, status, reason = _table_disposition(event, reporting_period)
        enriched = {
            **event,
            "event_status": status,
            "evidence_structure": structure.structure_type,
            "structure_quality": structure.structure_quality,
            "period_binding": structure.period_binding,
            "table_provenance": {
                "page": event.get("page_or_section"),
                "table_title": structure.table_title,
                "row_label": structure.row_label,
                "column_heading": structure.column_heading,
                "cell_value": structure.cell_value,
                "surrounding_context": event.get("nearby_context"),
            },
            "table_context_reason": reason,
        }
        if decision == "accepted":
            accepted.append(enriched)
        elif decision == "ambiguous":
            table_ambiguous.append(enriched)
        else:
            table_rejections.append(enriched)
    accounting_observations = [
        {
            "observation_type": "accounting_event_measure",
            "metric_label": item["table_provenance"]["row_label"],
            "reported_value": item["table_provenance"]["cell_value"],
            "period_binding": item["period_binding"],
            "source_span": item["source_span"],
            "page_or_section": item.get("page_or_section"),
            "operational_event_promoted": False,
        }
        for item in table_rejections
        if item["table_context_reason"] == "financial_observation_not_operational_event"
    ]
    observed_spans = {item["source_span"] for item in accounting_observations}
    for candidate in candidates:
        if candidate["source_span"] in observed_spans or not ACCOUNTING_ROW.search(candidate["source_span"]):
            continue
        values = _number_tokens(candidate["source_span"])
        if not values:
            continue
        accounting_observations.append({
            "observation_type": "accounting_event_measure",
            "metric_label": candidate["row_label"],
            "reported_value": candidate["cell_value"],
            "period_binding": candidate["period_binding"],
            "source_span": candidate["source_span"],
            "page_or_section": candidate.get("page_or_section"),
            "operational_event_promoted": any(
                event["source_span"] == candidate["source_span"] for event in accepted
            ),
        })
        observed_spans.add(candidate["source_span"])
    return {
        **base,
        "candidates": candidates,
        "accepted_events": accepted,
        "event_rejections": base["event_rejections"] + table_rejections,
        "ambiguous_events": base["ambiguous_events"] + table_ambiguous,
        "table_context_rejections": table_rejections,
        "table_context_ambiguous": table_ambiguous,
        "accounting_observations": accounting_observations,
    }


def extract_contextual_events_v032(
    text: str, *, publication_date: str | None = None, reporting_period: str | None = None
) -> list[dict]:
    pipeline = extract_event_pipeline(text, publication_date=publication_date, reporting_period=reporting_period)
    return [
        {
            "event_type": event["event_type"],
            "evidence_span": event["source_span"],
            "context_status": event["event_status"],
            "quantified": bool(re.search(r"\d", event["source_span"])),
            "scope": event["scope"],
            "confidence": event["confidence"],
            "candidate_ids": event["candidate_ids"],
            "evidence_structure": event["evidence_structure"],
            "period_binding": event["period_binding"],
            "table_provenance": event["table_provenance"],
        }
        for event in pipeline["accepted_events"]
    ]

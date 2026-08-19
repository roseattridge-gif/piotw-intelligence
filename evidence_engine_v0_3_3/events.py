from __future__ import annotations

import re
from dataclasses import dataclass

from evidence_engine_v0_3_2.events import extract_event_pipeline as extract_v032_pipeline

BIOGRAPHY = re.compile(
    r"\b(?:biograph|served as|previously (?:served|led|worked)|career at|former employer|"
    r"began (?:his|her|their) career|appointed to the board)\b", re.IGNORECASE
)
INDUSTRY_SUBJECT = re.compile(
    r"\b(?:the|our) (?:industry|sector|market)|industry participants|many other employers\b", re.IGNORECASE
)
SUPPLIER_SUBJECT = re.compile(
    r"\b(?:our |the )?(?:suppliers?|vendors?) (?:experienced|face|faced|may|might|could|can|plan|announced|expanded|reduced)\b",
    re.IGNORECASE,
)
CUSTOMER_SUBJECT = re.compile(
    r"\b(?:our |the )?customers? (?:experienced|face|faced|may|might|could|can|plan|announced|reduced|have|has|desire)\b",
    re.IGNORECASE,
)
COMPETITOR_SUBJECT = re.compile(r"\b(?:our |the )?competitors? (?:experienced|face|faced|may|could|plan|announced)\b", re.IGNORECASE)
THIRD_PARTY_PLAN = re.compile(r"^\s*(?!we\b|our\b|the company\b|the group\b)([A-Z][A-Za-z&.-]+) (?:plans?|announced|expects?) to\b")
QUOTE = re.compile(r"\b(?:according to|analysts? (?:said|expect)|a customer said|a supplier said|the regulator said)\b", re.IGNORECASE)
SUBSIDIARY = re.compile(r"\b(?:our|the company's|the group’s|the group's) (?:controlled )?subsidiary\b", re.IGNORECASE)
JOINT_VENTURE = re.compile(r"\b(?:joint venture|associate company)\b", re.IGNORECASE)
ACQUISITION_TARGET = re.compile(r"\bacquisition target\b", re.IGNORECASE)
SEGMENT = re.compile(r"\b(?:our |the )?([A-Z][A-Za-z& ]{2,40}) (?:segment|division|business unit)\b", re.IGNORECASE)
TARGET_REFERENCE = re.compile(r"\b(?:we|our|us|the company|the group|company's|group's)\b", re.IGNORECASE)
TARGET_IMPACT = re.compile(
    r"\b(?:caused|causing|resulted in|reduced|delayed|constrained|disrupted|affected|impact(?:ed|ing)) "
    r"(?:our|the company's|the group’s|the group's) (?:production|output|sales|volume|operations|deliveries|business)\b",
    re.IGNORECASE,
)
MODAL = re.compile(r"\b(?:may|might|could|can|would|should|potentially|risk of|possibility of|subject to|if)\b", re.IGNORECASE)
ACTUAL = re.compile(
    r"\b(?:currently|during the (?:quarter|period)|experienced|experiencing|has experienced|have experienced|"
    r"declined|decreased|reduced|constrained|disrupted|delayed|paused|increased|announced|initiated|implemented|"
    r"are at times subject to)\b",
    re.IGNORECASE,
)
GENERIC_RISK = re.compile(
    r"\b(?:other factors, including|can fluctuate|may face|could result|mitigate the risks? of|"
    r"sensitive to general economic conditions|the closure of .* involves|if .* were to|"
    r"are subject to|could adversely affect|enable us to capture revenue growth|future revenue growth rates|"
    r"shortages persist broadly|classified as essential.{0,100}facility closures?)\b",
    re.IGNORECASE,
)
TECHNICAL_REDUNDANCY = re.compile(r"\b(?:database|system|server|network).{0,100}\bredundan", re.IGNORECASE)
CUSTOMER_BENEFIT = re.compile(r"\b(?:cost reductions? for our customers|customers?.{0,120}cost reductions?)\b", re.IGNORECASE)
LOW_QUALITY_JOIN = re.compile(r"(?:^\s*\d+\s+table of contents\b|form 10-k table of contents)", re.IGNORECASE)
ACCOUNTING_CONTEXT = re.compile(
    r"\b(?:relate to, among other things|corporate includes|for purposes of business segment performance|"
    r"excluding .{0,80}(?:restructuring|integration|divestiture) costs?|"
    r"estimates? require judgment of future revenue growth|see note \d+ .{0,80}additional information)\b",
    re.IGNORECASE,
)
EQUITY_METHOD = re.compile(r"\b(?:equity method investment|unconsolidated affiliate)\b", re.IGNORECASE)
SUPPLIER_LABOUR = re.compile(r"\bsupplier.{0,100}\blabou?r shortages?\b", re.IGNORECASE)


@dataclass(frozen=True)
class SubjectAttribution:
    subject_type: str
    subject_entity: str | None
    target_company_relevance: str
    entity_scope: str
    segment_name: str | None
    geography: str | None
    facility_or_product: str | None
    status: str
    reason: str


def _risk_status(span: str) -> str:
    actual = bool(ACTUAL.search(span))
    modal = bool(MODAL.search(span))
    if re.search(r"\b(?:plan|plans|planned|expect to|announced)\b", span, re.IGNORECASE):
        return "planned"
    if re.search(r"\b(?:prior year|previously)\b", span, re.IGNORECASE):
        return "actual_historical"
    embedded_current = bool(re.search(r"\bafter (?:having )?(?:declined|decreased|falling).{0,60}\b(?:quarter|period|year)\b", span, re.IGNORECASE))
    actual_subject_to = bool(re.search(r"\bare at times subject to\b", span, re.IGNORECASE))
    if GENERIC_RISK.search(span) and not TARGET_IMPACT.search(span) and not embedded_current and not actual_subject_to:
        return "generic_risk"
    if modal and not actual:
        return "hypothetical_risk"
    if actual and modal:
        return "actual_current_with_forecast"
    if actual:
        return "actual_current"
    return "ambiguous"


def attribute_subject(span: str, nearby_context: str = "") -> SubjectAttribution:
    combined = f"{nearby_context} {span}"
    segment = SEGMENT.search(span)
    segment_name = next((group for group in segment.groups() if group), None) if segment else None
    if BIOGRAPHY.search(combined):
        return SubjectAttribution("former_employer", None, "external", "external", None, None, None, _risk_status(span), "biography_or_career_history")
    if QUOTE.search(span):
        return SubjectAttribution("third_party", None, "external", "external", None, None, None, _risk_status(span), "third_party_quote")
    if CUSTOMER_BENEFIT.search(span) or CUSTOMER_SUBJECT.search(span):
        if TARGET_IMPACT.search(span):
            return SubjectAttribution("target_company", None, "direct", "group_or_unspecified", None, None, None, _risk_status(span), "customer_condition_with_explicit_company_impact")
        return SubjectAttribution("customer", None, "external", "external", None, None, None, _risk_status(span), "customer_is_grammatical_subject")
    if SUPPLIER_SUBJECT.search(span):
        if TARGET_IMPACT.search(span):
            return SubjectAttribution("target_company", None, "direct", "group_or_unspecified", None, None, None, _risk_status(span), "supplier_cause_with_explicit_company_impact")
        return SubjectAttribution("supplier", None, "external", "external", None, None, None, _risk_status(span), "supplier_is_grammatical_subject")
    if COMPETITOR_SUBJECT.search(span):
        return SubjectAttribution("competitor", None, "external", "external", None, None, None, _risk_status(span), "competitor_is_grammatical_subject")
    if INDUSTRY_SUBJECT.search(span):
        return SubjectAttribution("industry", None, "external", "sector", None, None, None, _risk_status(span), "industry_level_statement")
    third_party = THIRD_PARTY_PLAN.search(span)
    if third_party:
        return SubjectAttribution("third_party", third_party.group(1), "external", "external", None, None, None, _risk_status(span), "named_third_party_is_subject")
    if JOINT_VENTURE.search(span):
        return SubjectAttribution("joint_venture", None, "external_or_shared", "joint_venture", None, None, None, _risk_status(span), "joint_venture_subject")
    if ACQUISITION_TARGET.search(span):
        return SubjectAttribution("acquisition_target", None, "external", "external", None, None, None, _risk_status(span), "acquisition_target_subject")
    if SUBSIDIARY.search(span):
        return SubjectAttribution("target_subsidiary", None, "direct", "subsidiary", None, None, None, _risk_status(span), "controlled_subsidiary_reference")
    if segment_name:
        return SubjectAttribution("target_segment", segment_name.strip(), "direct", "segment", segment_name.strip(), None, None, _risk_status(span), "named_target_segment")
    if TARGET_REFERENCE.search(span) or TARGET_REFERENCE.search(nearby_context):
        return SubjectAttribution("target_company", None, "direct", "group_or_unspecified", None, None, None, _risk_status(span), "issuer_reference")
    if ACTUAL.search(span):
        return SubjectAttribution("target_company", None, "inferred", "group_or_unspecified", None, None, None, _risk_status(span), "factual_filing_clause_without_external_subject")
    return SubjectAttribution("unknown", None, "unclear", "unknown", None, None, None, _risk_status(span), "subject_not_resolved")


def _acceptance(subject: SubjectAttribution, event: dict) -> tuple[str, str]:
    span = event["source_span"]
    if TECHNICAL_REDUNDANCY.search(span):
        return "rejected", "technical_redundancy_not_workforce_event"
    if LOW_QUALITY_JOIN.search(span) and len(span) > 280:
        return "rejected", "joined_page_table_fragment"
    if ACCOUNTING_CONTEXT.search(span):
        return "rejected", "accounting_definition_or_cross_reference"
    if EQUITY_METHOD.search(span):
        return "rejected", "external_equity_method_or_affiliate_context"
    if event["event_type"] == "labour_constraint" and SUPPLIER_LABOUR.search(span) and not TARGET_IMPACT.search(span):
        return "rejected", "supplier_labour_condition_without_target_labour_event"
    if subject.subject_type in {"supplier", "customer", "competitor", "industry", "third_party", "former_employer", "acquisition_target", "joint_venture"}:
        return "rejected", f"external_subject:{subject.subject_type}"
    if subject.subject_type == "unknown":
        return "ambiguous", "subject_unresolved"
    if subject.status in {"generic_risk", "hypothetical_risk"}:
        return "rejected", subject.status
    if subject.status == "actual_historical":
        return "rejected", "historical_condition"
    return "accepted", "acceptance_contract_satisfied"


def extract_event_pipeline(text: str, *, publication_date: str | None = None,
                           reporting_period: str | None = None,
                           page_or_section: str | None = None) -> dict:
    base = extract_v032_pipeline(text, publication_date=publication_date,
                                 reporting_period=reporting_period, page_or_section=page_or_section)
    accepted, rejected, ambiguous = [], [], []
    for event in base["accepted_events"]:
        subject = attribute_subject(event["source_span"], event.get("nearby_context", ""))
        if event["event_type"] in {"labour_constraint", "supply_chain_constraint"} and (
            SUPPLIER_SUBJECT.search(event["source_span"]) or SUPPLIER_LABOUR.search(event["source_span"])
        ):
            subject = SubjectAttribution("supplier", None, "external", "external", None, None, None,
                subject.status, "supplier_condition_separated_from_target_company_impact")
        decision, reason = _acceptance(subject, event)
        enriched = {**event, "subject_type": subject.subject_type,
            "subject_entity": subject.subject_entity,
            "target_company_relevance": subject.target_company_relevance,
            "entity_scope": subject.entity_scope, "segment_name": subject.segment_name,
            "geography": subject.geography, "facility_or_product": subject.facility_or_product,
            "factual_status": subject.status, "subject_attribution_reason": subject.reason,
            "acceptance_contract_reason": reason}
        if decision == "accepted": accepted.append(enriched)
        elif decision == "ambiguous": ambiguous.append(enriched)
        else: rejected.append(enriched)
    return {**base, "accepted_events": accepted,
        "event_rejections": base["event_rejections"] + rejected,
        "ambiguous_events": base["ambiguous_events"] + ambiguous,
        "entity_context_rejections": rejected, "entity_context_ambiguous": ambiguous}


def extract_contextual_events_v033(text: str, *, publication_date: str | None = None,
                                   reporting_period: str | None = None) -> list[dict]:
    pipeline = extract_event_pipeline(text, publication_date=publication_date, reporting_period=reporting_period)
    return [{"event_type": event["event_type"], "evidence_span": event["source_span"],
        "context_status": event["event_status"], "quantified": bool(re.search(r"\d", event["source_span"])),
        "scope": event["scope"], "confidence": event["confidence"],
        "candidate_ids": event["candidate_ids"], "subject_type": event["subject_type"],
        "entity_scope": event["entity_scope"], "factual_status": event["factual_status"]}
        for event in pipeline["accepted_events"]]

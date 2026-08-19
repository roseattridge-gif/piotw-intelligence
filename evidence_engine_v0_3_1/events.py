from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher

EVENT_PATTERNS = {
    "cost_reduction": [r"cost[- ]?(?:reduction|saving)s?", r"reducing discretionary spending", r"reduc(?:e|ed|es|ing) operating costs"],
    "restructuring": [r"restructur(?:e|ed|ing|ing programme|ing program)"],
    "efficiency_programme": [r"efficiency (?:programme|program|initiative)"],
    "simplification": [r"simplification (?:programme|program|initiative)", r"simplif(?:y|ied|ying) (?:the )?(?:business|operations)"],
    "transformation": [r"transformation (?:programme|program|initiative)", r"business transformation"],
    "demand_weakness": [r"(?:weak|weaker|declining|lower|soft) demand", r"net sales decreased", r"backlog .*?decreased", r"orders? (?:declined|decreased)"],
    "supply_chain_constraint": [r"supply.chain (?:constraint|disruption|shortage|pressure)s?", r"industry-wide shortage", r"component shortages?"],
    "labour_constraint": [r"labou?r (?:constraint|shortage|scarcity)", r"work stoppage", r"strike .*?(?:paused|slowed|disrupted)"],
    "operational_disruption": [r"operational disruption", r"production (?:disruption|paused|was paused)", r"(?:slowed|paused) production", r"production and deliveries were (?:slowed|paused)"],
    "capacity_reduction": [r"capacity reduction", r"reduc(?:e|ed|ing) capacity"],
    "site_closure": [r"(?:site|plant|facility) closure", r"clos(?:e|ed|ing) (?:a |the )?(?:site|plant|facility)"],
    "redundancy": [r"redundan(?:cy|cies|t)"],
    "workforce_reduction": [r"workforce (?:reduction|by roughly|by approximately)", r"reduce the size of (?:our|the) (?:total )?workforce", r"reduc(?:e|ed|ing) headcount"],
    "refinancing": [r"refinanc(?:e|ed|ing)"],
    "liquidity_concern": [r"liquidity (?:concern|constraint|pressure)", r"ratings? (?:were )?downgraded", r"placed .*?ratings? on review for downgrade"],
    "growth_language": [r"(?:revenue|sales|volume|net sales) (?:grew|growth|increased)", r"strong growth"],
    "recovery_language": [r"recover(?:ed|y|ing) to (?:pre-pandemic|prior)", r"recovery (?:continued|strengthened|underway)"],
    "order_book_strength": [r"(?:strong|record|growing) order.book"],
    "capacity_expansion": [r"capacity expansion", r"expand(?:ed|ing) capacity", r"new or expanded (?:equipment|facilities|properties)"],
    "major_investment": [r"major investment", r"investment programme", r"(?:we )?expect (?:our )?capital expenditures? to be", r"substantial investments? in new or expanded"],
    "new_facility": [r"new (?:facility|plant|factory|site)"],
    "margin_deterioration": [r"downward pressure on (?:gross )?margins?", r"pricing pressure", r"pressures? on pricing", r"margin (?:declined|fell|deteriorated)"],
}

NEGATION = re.compile(r"\b(?:no|not|without|avoided|prevented|did not|no plans? to|unlikely to)\b", re.IGNORECASE)
HYPOTHETICAL = re.compile(r"\b(?:may|might|could|potentially|risk of|possibility|if|should)\b", re.IGNORECASE)
ACTUAL = re.compile(r"\b(?:have experienced|has experienced|is experiencing|currently|ongoing|announced|actions we have taken|we are reducing|has reduced|have reduced|was reduced|were reduced|declined|decreased|increased|recovered|paused|slowed|downgraded|have resulted|has resulted|has had)\b", re.IGNORECASE)
PLANNED = re.compile(r"\b(?:plan(?:ned|s)? to|planned (?:workforce|site|facility|capacity|investment)|expect(?:ed)? to|intend(?:ed)? to|will |announced (?:a )?plan)\b", re.IGNORECASE)
COMPLETED = re.compile(r"\b(?:completed|was completed|previously announced|formerly|last year|prior year|historical)\b", re.IGNORECASE)
BIOGRAPHY = re.compile(r"\b(?:served as|began (?:his|her|their) career|career at|where (?:he|she|they) worked|previous employers?)\b", re.IGNORECASE)
GENERIC_ACCOUNTING = re.compile(r"\b(?:may include|these .*?items .*?include|these items consist of|assumptions?.*?(?:revenue growth|margin)|deemed to be significant assumptions?|for purposes of this definition|accounting for employee separations|additional information .*?restructuring costs|bar titled .*?restructuring|performance metric .*?revenue growth|troubled debt restructur|critical to achieving revenue growth)\b", re.IGNORECASE)
CONTINUITY_REDUNDANCY = re.compile(r"redundancy and other continuity|system upgrades, redundancy", re.IGNORECASE)
CALCULATION_SIMPLIFICATION = re.compile(r"as a simplification|simplification,? to calculate", re.IGNORECASE)
ENTITY = re.compile(r"\b(?:we|our|us|the company|the group|company's|group's)\b", re.IGNORECASE)
THIRD_PARTY = re.compile(r"\b(?:competitors?|customers?|suppliers?|vendors?|third part(?:y|ies)|acquisition target)\b", re.IGNORECASE)


@dataclass(frozen=True)
class CandidateEvent:
    candidate_id: str
    event_type: str
    matched_term: str
    source_span: str
    nearby_context: str
    page_or_section: str | None
    entity_reference: str
    publication_date: str | None
    reporting_period: str | None


@dataclass(frozen=True)
class ContextAssessment:
    candidate_id: str
    decision: str
    event_status: str
    entity_relevance: str
    scope: str
    negated: bool
    hypothetical: bool
    historical_or_completed: bool
    structural_zone: str | None
    acceptance_reason: str | None
    rejection_reason: str | None
    possible_mappings: tuple[str, ...]
    confidence: float


@dataclass(frozen=True)
class AcceptedEvent:
    event_id: str
    candidate_ids: tuple[str, ...]
    event_type: str
    event_status: str
    entity_relevance: str
    scope: str
    source_span: str
    nearby_context: str
    page_or_section: str | None
    event_period: str | None
    first_observed: str | None
    source_publication_date: str | None
    confidence: float
    deduplication_reason: str | None = None


def sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\s+\|\s+", text) if 20 <= len(part.strip()) <= 1200]


def generate_candidates(text: str, *, publication_date: str | None = None,
                        reporting_period: str | None = None,
                        page_or_section: str | None = None) -> list[CandidateEvent]:
    parts = sentences(text)
    candidates = []
    for sentence_index, sentence in enumerate(parts):
        context = " ".join(parts[max(0, sentence_index - 1):sentence_index + 2])
        for event_type, patterns in EVENT_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, sentence, re.IGNORECASE):
                    candidates.append(CandidateEvent(
                        candidate_id=f"candidate-{len(candidates) + 1:05d}", event_type=event_type,
                        matched_term=match.group(0), source_span=sentence, nearby_context=context,
                        page_or_section=page_or_section,
                        entity_reference="target_company" if ENTITY.search(sentence) else "context_inherited",
                        publication_date=publication_date, reporting_period=reporting_period))
    return candidates


def _scope(sentence: str) -> str:
    lowered = sentence.lower()
    if any(token in lowered for token in ("greater china", "segment", "division", "business unit", "bgs ")):
        return "segment_or_geography"
    if any(token in lowered for token in ("facility", "plant", "site")):
        return "facility"
    if "supplier" in lowered or "vendor" in lowered:
        return "supplier_context"
    return "group_or_unspecified"


def _explicit_year_status(sentence: str, reporting_period: str | None) -> str | None:
    years = re.findall(r"\b(20\d{2})\b", sentence)
    if not years or not reporting_period:
        return None
    report_year = reporting_period[:4]
    if report_year in years:
        return "current"
    return "future" if max(map(int, years)) > int(report_year) else "historical"


def assess_candidate(candidate: CandidateEvent) -> ContextAssessment:
    sentence = candidate.source_span
    context = candidate.nearby_context
    scope = _scope(sentence)
    structural = "biography" if BIOGRAPHY.search(context) else "accounting_or_definition" if GENERIC_ACCOUNTING.search(sentence) else None
    negated = bool(NEGATION.search(sentence))
    actual = bool(ACTUAL.search(sentence))
    hypothetical = bool(HYPOTHETICAL.search(sentence)) and not actual
    explicit_year = _explicit_year_status(sentence, candidate.reporting_period)
    historical = bool(COMPLETED.search(sentence)) or explicit_year == "historical"
    planned = bool(PLANNED.search(sentence)) or explicit_year == "future"
    entity = "target_company" if ENTITY.search(context) else "third_party" if THIRD_PARTY.search(sentence) else "unclear"
    reason = None
    decision = "accepted"
    status = "planned" if planned else "ongoing" if "ongoing" in sentence.lower() else "current"
    confidence = 0.9
    if structural:
        decision, status, reason, confidence = "rejected", "background", structural, 0.98
    elif candidate.event_type == "redundancy" and CONTINUITY_REDUNDANCY.search(sentence):
        decision, status, reason, confidence = "rejected", "irrelevant", "business_continuity_redundancy_not_workforce", 0.99
    elif candidate.event_type == "simplification" and CALCULATION_SIMPLIFICATION.search(sentence):
        decision, status, reason, confidence = "rejected", "irrelevant", "calculation_wording_not_company_event", 0.99
    elif negated:
        decision, status, reason, confidence = "rejected", "negated", "explicit_negation", 0.98
    elif historical and not planned:
        decision, status, reason, confidence = "rejected", "historical", "historical_or_completed", 0.94
    elif hypothetical:
        decision, status, reason, confidence = "rejected", "hypothetical", "generic_or_hypothetical_risk", 0.92
    elif entity == "third_party":
        decision, status, reason, confidence = "rejected", "third_party", "wrong_entity", 0.9
    elif entity == "unclear" and not actual and not planned:
        decision, status, reason, confidence = "ambiguous", "ambiguous", "entity_or_factuality_unclear", 0.55
    acceptance = None if decision != "accepted" else "direct factual support with target-company or inherited context"
    return ContextAssessment(candidate.candidate_id, decision, status, entity, scope, negated,
        hypothetical, historical, structural, acceptance, reason, (candidate.event_type,), confidence)


def _similarity(left: str, right: str) -> float:
    normalized = lambda value: re.sub(r"\W+", " ", value.lower()).strip()
    return SequenceMatcher(None, normalized(left), normalized(right)).ratio()


def deduplicate(events: list[AcceptedEvent]) -> tuple[list[AcceptedEvent], list[dict]]:
    kept: list[AcceptedEvent] = []
    links = []
    for event in events:
        duplicate_of = next((prior for prior in kept if prior.event_type == event.event_type
            and prior.scope == event.scope and prior.event_period == event.event_period
            and _similarity(prior.source_span, event.source_span) >= 0.86), None)
        if duplicate_of:
            links.append({"duplicate_event_id": event.event_id, "canonical_event_id": duplicate_of.event_id,
                          "reason": "same document/type/scope/period with highly overlapping evidence"})
            continue
        kept.append(event)
    return kept, links


def extract_event_pipeline(text: str, *, publication_date: str | None = None,
                           reporting_period: str | None = None,
                           page_or_section: str | None = None) -> dict:
    candidates = generate_candidates(text, publication_date=publication_date,
                                     reporting_period=reporting_period, page_or_section=page_or_section)
    assessments = [assess_candidate(candidate) for candidate in candidates]
    by_id = {candidate.candidate_id: candidate for candidate in candidates}
    accepted = []
    for assessment in assessments:
        if assessment.decision != "accepted":
            continue
        candidate = by_id[assessment.candidate_id]
        accepted.append(AcceptedEvent(event_id=f"event-{len(accepted) + 1:05d}",
            candidate_ids=(candidate.candidate_id,), event_type=candidate.event_type,
            event_status=assessment.event_status, entity_relevance=assessment.entity_relevance,
            scope=assessment.scope, source_span=candidate.source_span,
            nearby_context=candidate.nearby_context, page_or_section=candidate.page_or_section,
            event_period=reporting_period, first_observed=publication_date,
            source_publication_date=publication_date, confidence=assessment.confidence))
    deduped, links = deduplicate(accepted)
    return {"candidates": [asdict(item) for item in candidates],
            "assessments": [asdict(item) for item in assessments],
            "accepted_events": [asdict(item) for item in deduped],
            "event_rejections": [asdict(item) for item in assessments if item.decision == "rejected"],
            "ambiguous_events": [asdict(item) for item in assessments if item.decision == "ambiguous"],
            "deduplication_links": links}


def extract_contextual_events_v031(text: str, *, publication_date: str | None = None,
                                   reporting_period: str | None = None) -> list[dict]:
    pipeline = extract_event_pipeline(text, publication_date=publication_date, reporting_period=reporting_period)
    return [{"event_type": event["event_type"], "evidence_span": event["source_span"],
             "context_status": event["event_status"], "quantified": bool(re.search(r"\d", event["source_span"])),
             "scope": event["scope"], "confidence": event["confidence"],
             "candidate_ids": event["candidate_ids"]} for event in pipeline["accepted_events"]]

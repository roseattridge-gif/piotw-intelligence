from __future__ import annotations

import re
from dataclasses import replace
from typing import ClassVar

from evidence_engine_v0_3_4.semantic import (
    DeterministicSemanticVerifier,
    SemanticCandidate,
    SemanticDecision,
)

MANDATORY_SUFFICIENCY_FIELDS = ("subject", "predicate", "actuality", "timing", "target_relevance", "definition_fit")


def classify_source_zone(heading: str | None, span: str) -> str:
    value = f"{heading or ''} {span}".lower()
    if re.search(r"\b(directors?|officers?|biograph|board of directors|executive profile)\b", value):
        return "biography"
    if re.search(r"\b(accounting polic|basis of preparation|non-gaap|alternative performance measure|definitions?)\b", value):
        return "accounting_definition"
    if re.search(r"\b(legal proceedings?|litigation|contingencies|claims and actions)\b", value):
        return "legal"
    if re.search(r"\b(risk factors?|principal risks?)\b", value):
        return "risk"
    if re.search(r"\b(table|£m|\$m|€m|year ended)\b", value) and "\n" in span:
        return "table_or_fragment"
    return "body_narrative"


def evidence_sufficiency(candidate: SemanticCandidate) -> dict[str, bool]:
    span = candidate.exact_candidate_span.strip()
    meta = candidate.deterministic_metadata
    subject_type = meta.get("subject_type", "unknown")
    actual = not bool(re.search(
        r"\b(?:may|might|could|would|risk of|possibility of|if (?:we|the company|the group))\b", span,
        re.IGNORECASE,
    )) or bool(re.search(r"\b(?:experienced|occurred|reduced|increased|declined|initiated|implemented|closed|opened|paused)\b", span, re.IGNORECASE))
    complete_sentence = bool(re.search(r"[.!?]$", span)) and len(span.split()) >= 5
    event_terms = bool(re.search(
        r"\b(?:restructur|clos|open|expand|reduc|increase|declin|deteriorat|improv|pressure|constraint|disrupt|programme|program|backlog|capacity|hiring|vacanc|margin|revenue|price|pricing)\w*\b",
        span, re.IGNORECASE,
    ))
    timing = bool(meta.get("event_status")) or bool(re.search(
        r"\b(?:during|in|since|currently|ongoing|this year|the year|quarter|month|planned|announced|completed|previously)\b", span, re.IGNORECASE,
    ))
    return {
        "subject": subject_type in {"target_company", "target_segment", "target_subsidiary"},
        "predicate": complete_sentence and event_terms,
        "actuality": actual and meta.get("factual_status") not in {"generic_risk", "hypothetical_risk"},
        "timing": timing,
        "target_relevance": subject_type in {"target_company", "target_segment", "target_subsidiary"},
        "definition_fit": event_terms,
    }


def polarity_for(candidate: SemanticCandidate) -> str:
    span = candidate.exact_candidate_span.lower()
    positive = re.search(r"\b(?:increase[ds]?|grew|growth|improv(?:e|ed|ement)|accelerat(?:e|ed|ion)|expand(?:ed|ing|sion)|open(?:ed|ing))\b", span)
    negative = re.search(r"\b(?:decrease[ds]?|declin(?:e|ed)|deteriorat(?:e|ed|ion)|contract(?:ed|ion)|reduc(?:e|ed|tion)|pressure|clos(?:e|ed|ure))\b", span)
    if positive and negative:
        return "mixed"
    if positive:
        return "increase_or_improvement"
    if negative:
        return "decrease_or_deterioration"
    return "not_directional_or_unknown"


class DeterministicSemanticVerifierV035(DeterministicSemanticVerifier):
    model_version = "semantic-rules-v0.3.5-development"
    prompt_version = "semantic-event-v0.3.5-development"

    GENERAL_EXCLUSIONS: ClassVar[list[tuple[str, str]]] = [
        ("HEADING_ONLY", r"^\s*(?:\(?\d+\)?\s*)?(?:cost savings plans?|restructuring|site closures?|capacity|pricing pressure)\.?\s*$"),
        ("LEGAL_REFERENCE", r"\b(?:claims and actions arising from|legal proceedings? (?:include|involve)|litigation relating to)\b"),
        ("ACCOUNTING_DEFINITION", r"\b(?:represent(?:s)? gross reductions|is defined as|are defined as|for accounting purposes|means the amount|consist(?:s)? of charges)\b"),
        ("THIRD_PARTY_ONLY", r"\b(?:the global economy|the industry|competitors?|quoted analyst|the customer|the supplier)\b.{0,100}\b(?:experienced|announced|closed|restructured|disruption)\b"),
        ("GENERIC_RISK", r"\b(?:may be subject to|could be affected by|risk of|possibility of|may adversely affect)\b"),
        ("WRONG_CONTEXT", r"\b(?:operating expenses?|costs?)\b.{0,80}\b(?:grew|growth|increased)\b|\bnet revenue growth has been impacted\b"),
    ]

    def verify(self, candidate: SemanticCandidate) -> SemanticDecision:
        span = candidate.exact_candidate_span
        zone = candidate.deterministic_metadata.get("source_zone") or classify_source_zone(candidate.heading, span)
        for reason, pattern in self.GENERAL_EXCLUSIONS:
            if re.search(pattern, span, re.IGNORECASE | re.DOTALL):
                meta = {**candidate.deterministic_metadata, "factual_status": (
                    "hypothetical_risk" if reason == "GENERIC_RISK" else candidate.deterministic_metadata.get("factual_status")),
                    "source_zone": zone}
                if reason == "THIRD_PARTY_ONLY":
                    meta["subject_type"] = "industry_or_third_party"
                candidate = replace(candidate, deterministic_metadata=meta)
                decision = super().verify(candidate)
                if decision.reason_code != reason and reason in {"HEADING_ONLY", "LEGAL_REFERENCE", "ACCOUNTING_DEFINITION", "THIRD_PARTY_ONLY", "GENERIC_RISK", "WRONG_CONTEXT"}:
                    raw = {
                        "decision": "reject", "event_type": None,
                        "subject_type": meta.get("subject_type", "unknown"),
                        "event_status": "hypothetical" if reason == "GENERIC_RISK" else "ambiguous",
                        "scope": None, "evidence_supported": False, "exact_support_span": None,
                        "reason_code": reason,
                        "short_reason": "The evidence does not directly establish an actual target-company event.",
                    }
                    return SemanticDecision.from_dict(raw, provider=self.provider, model_version=self.model_version,
                        prompt_version=self.prompt_version, candidate=candidate)
                return replace(decision, model_version=self.model_version, prompt_version=self.prompt_version)

        sufficiency = evidence_sufficiency(candidate)
        missing = [key for key in MANDATORY_SUFFICIENCY_FIELDS if not sufficiency[key]]
        if missing:
            ambiguous_only = set(missing) <= {"timing"}
            raw = {
                "decision": "ambiguous" if ambiguous_only else "reject",
                "event_type": None,
                "subject_type": candidate.deterministic_metadata.get("subject_type", "unknown"),
                "event_status": "ambiguous", "scope": None, "evidence_supported": False,
                "exact_support_span": None,
                "reason_code": "TIMING_AMBIGUOUS" if ambiguous_only else "INSUFFICIENT_SUPPORT",
                "short_reason": "Evidence sufficiency failed: " + ", ".join(missing),
            }
            return SemanticDecision.from_dict(raw, provider=self.provider, model_version=self.model_version,
                prompt_version=self.prompt_version, candidate=candidate)
        decision = super().verify(candidate)
        return replace(decision, model_version=self.model_version, prompt_version=self.prompt_version)

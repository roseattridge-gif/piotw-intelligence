from __future__ import annotations

import re

EVENT_PATTERNS = {
    "cost_reduction": r"cost(?: |-)(?:reduction|saving)",
    "restructuring": r"restructur(?:e|ed|ing)",
    "efficiency_programme": r"efficiency (?:programme|program|initiative)",
    "simplification": r"simplif(?:y|ication)",
    "transformation": r"transformation (?:programme|program|initiative)",
    "demand_weakness": r"(?:weak|weaker|declining|lower|soft) demand",
    "supply_chain_constraint": r"supply.chain (?:constraint|disruption|shortage|pressure)",
    "labour_constraint": r"labou?r (?:constraint|shortage|scarcity)",
    "capacity_reduction": r"(?:capacity reduction|reduce(?:d|ing) capacity)",
    "site_closure": r"(?:site|plant|facility) closure|clos(?:e|ed|ing) (?:a |the )?(?:site|plant|facility)",
    "redundancy": r"redundan(?:cy|cies|t)",
    "refinancing": r"refinanc(?:e|ed|ing)",
    "liquidity_concern": r"liquidity (?:concern|constraint|pressure)",
    "growth_language": r"(?:revenue|sales|volume) growth|strong growth",
    "order_book_strength": r"(?:strong|record|growing) order.book",
    "capacity_expansion": r"capacity expansion|expand(?:ed|ing) capacity",
    "major_investment": r"major investment|investment programme|investment program",
    "new_facility": r"new (?:facility|plant|factory|site)",
}
EVENT_GROUPS = {
    "cost_reduction": "intervention", "restructuring": "intervention",
    "efficiency_programme": "intervention", "simplification": "intervention",
    "transformation": "intervention", "capacity_reduction": "intervention",
    "site_closure": "intervention", "redundancy": "intervention",
    "demand_weakness": "operational_pressure", "supply_chain_constraint": "operational_pressure",
    "labour_constraint": "operational_pressure", "liquidity_concern": "financial_pressure",
    "refinancing": "financial_pressure", "growth_language": "contrary_strength",
    "order_book_strength": "contrary_strength", "capacity_expansion": "expansion",
    "major_investment": "expansion", "new_facility": "expansion",
}
NEGATION = re.compile(r"\b(?:no|not|without|neither|nor)\b", re.IGNORECASE)
HISTORICAL = re.compile(r"\b(?:completed|previously announced|announced in 20\d\d|last year|prior year|following the)\b", re.IGNORECASE)


def candidate_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if 20 <= len(part.strip()) <= 1000]


def context_status(sentence: str, match_start: int) -> str:
    before = sentence[max(0, match_start - 100):match_start]
    if NEGATION.search(before):
        return "negated"
    if HISTORICAL.search(sentence):
        return "historical_or_completed"
    return "current_or_general"


def extract_contextual_events(text: str) -> list[dict]:
    events = []
    seen = set()
    for sentence in candidate_sentences(text):
        for event_type, pattern in EVENT_PATTERNS.items():
            for match in re.finditer(pattern, sentence, re.IGNORECASE):
                status = context_status(sentence, match.start())
                key = (event_type, " ".join(sentence.lower().split()))
                if key in seen or status != "current_or_general":
                    continue
                seen.add(key)
                events.append({"event_type": event_type, "evidence_span": sentence,
                               "context_status": status, "quantified": bool(re.search(r"\d", sentence))})
    return events

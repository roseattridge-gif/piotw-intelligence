from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date


def event_fingerprint(company_id: str, event_type: str, event_date: date, summary: str) -> str:
    tokens = sorted(set(re.findall(r"[a-z0-9]+", summary.casefold())))
    week = event_date.isocalendar()[:2]
    canonical = f"{company_id}|{event_type}|{week[0]}-{week[1]}|{' '.join(tokens)}"
    return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass(frozen=True)
class EventCandidate:
    company_id: str
    event_type: str
    event_date: date
    summary: str


def token_similarity(left: str, right: str) -> float:
    a = set(re.findall(r"[a-z0-9]+", left.casefold()))
    b = set(re.findall(r"[a-z0-9]+", right.casefold()))
    return len(a & b) / len(a | b) if a | b else 1.0


def same_event(left: EventCandidate, right: EventCandidate, threshold: float = 0.65) -> bool:
    return (left.company_id == right.company_id and left.event_type == right.event_type
            and abs((left.event_date - right.event_date).days) <= 14
            and token_similarity(left.summary, right.summary) >= threshold)

from __future__ import annotations

import hashlib
import re
from datetime import date

from .models import EvidenceZone

OPERATIONAL_TERMS = re.compile(
    r"\b(?:sales|revenue|volume|backlog|demand|margin|cost|restructur|severance|workforce|"
    r"employee|appoint|facility|plant|site|capacity|production|supply|supplier|inventory|"
    r"recall|quality|regulator|closure|opened|disruption|investment|charges?)\b",
    re.IGNORECASE,
)
QUANTITATIVE_CHANGE = re.compile(r"(?:\$|£|€|\b\d+(?:\.\d+)?%|\b(?:increased|decreased|grew|declined|reduced)\b)", re.IGNORECASE)


def select_evidence_zones(*, company_id: str, source_id: str, publication_date: date, text: str) -> list[EvidenceZone]:
    """Select broad bounded passages without assigning event identity or product dimensions."""
    digest = hashlib.sha256(text.encode()).hexdigest()
    zones: list[EvidenceZone] = []
    for index, match in enumerate(re.finditer(r"[^\n]+(?:\n|$)", text)):
        paragraph = match.group().strip()
        if not paragraph:
            continue
        reasons = []
        if OPERATIONAL_TERMS.search(paragraph):
            reasons.append("operational_language")
        if QUANTITATIVE_CHANGE.search(paragraph):
            reasons.append("quantitative_or_directional_change")
        if not reasons:
            continue
        zones.append(EvidenceZone(
            zone_id=f"ez-{digest[:12]}-{index:04d}", company_id=company_id, source_id=source_id,
            source_hash=digest, publication_date=publication_date, text=paragraph,
            start=match.start(), end=match.start() + len(paragraph), selection_reasons=reasons,
        ))
    return zones

from __future__ import annotations

import re
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from intelligence.models import EvidenceObservation


FUNCTION_PATTERNS = {
    "operations": re.compile(r"\b(operations?|production|plant|manufactur|maintenance|lean|opex)\b", re.I),
    "quality": re.compile(r"\b(quality|validation|regulatory|compliance|assurance|hse|ehs)\b", re.I),
    "supply_chain": re.compile(r"\b(supply chain|procurement|buyer|purchasing|sourcing|logistics|planning)\b", re.I),
    "transformation": re.compile(r"\b(transformation|erp|sap|data|automation|digital|change|pmo)\b", re.I),
    "senior": re.compile(r"\b(chief|director|head|vice president|vp|general manager)\b", re.I),
}


def _strength_from_share(share: float) -> float:
    return min(1.0, share / 0.40)


def career_observations(database: str | Path, company_id: str, as_of_date: date) -> list[EvidenceObservation]:
    """Create conservative features from snapshots; requires at least one successful snapshot."""
    with sqlite3.connect(database) as connection:
        snapshots = connection.execute(
            "SELECT observed_at, open_job_count FROM career_snapshots "
            "WHERE company_id=? AND date(observed_at)<=? ORDER BY observed_at",
            (company_id, as_of_date.isoformat()),
        ).fetchall()
        jobs = connection.execute(
            "SELECT title, department, description, source_url, first_seen_at FROM career_jobs "
            "WHERE company_id=? AND date(first_seen_at)<=? AND (closed_at IS NULL OR date(closed_at)>?)",
            (company_id, as_of_date.isoformat(), as_of_date.isoformat()),
        ).fetchall()
    if not snapshots:
        return []

    observed_at = datetime.fromisoformat(snapshots[-1][0])
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=timezone.utc)
    total = snapshots[-1][1]
    rows: list[EvidenceObservation] = []

    if len(snapshots) >= 2:
        previous = snapshots[-2][1]
        change = (total - previous) / max(previous, 1)
        rows.append(EvidenceObservation(
            observation_id=f"{company_id}:vacancy-acceleration:{observed_at.date()}", company_id=company_id,
            family="workforce_demand_skills", feature="vacancy_acceleration", event_date=observed_at.date(),
            available_at=observed_at, source_type="ats_snapshot", source_url="local://career-snapshot",
            source_name="Configured public careers source", source_is_company_controlled=True,
            event_cluster_id=f"{company_id}:careers:{observed_at.date()}",
            direction_pressure=0.25 if change > 0 else 0, direction_expansion=1 if change > 0 else -0.5,
            strength=min(1.0, abs(change)), source_reliability=0.60, measurement_quality=0.70,
            materiality=min(1.0, abs(change)), independence=1.0, raw_value=round(change, 4), unit="ratio",
            explanation=f"Open vacancies changed from {previous} to {total} between successful snapshots.",
            extraction_method="deterministic_snapshot_delta"))

    combined = [(title or "") + " " + (department or "") + " " + (description or "")
                for title, department, description, _, _ in jobs]
    mapping = {
        "operations": ("operations_role_share", 0.35, 0.65),
        "quality": ("quality_role_share", 0.75, 0.25),
        "supply_chain": ("supply_chain_role_share", 0.70, 0.30),
        "transformation": ("transformation_role_share", 0.35, 1.0),
        "senior": ("seniority_shift", 0.45, 0.65),
    }
    for label, (feature, pressure_direction, expansion_direction) in mapping.items():
        count = sum(bool(FUNCTION_PATTERNS[label].search(text)) for text in combined)
        share = count / total if total else 0
        if count == 0:
            continue
        rows.append(EvidenceObservation(
            observation_id=f"{company_id}:{feature}:{observed_at.date()}", company_id=company_id,
            family="workforce_demand_skills", feature=feature, event_date=observed_at.date(),
            available_at=observed_at, source_type="ats_snapshot", source_url="local://career-snapshot",
            source_name="Configured public careers source", source_is_company_controlled=True,
            event_cluster_id=f"{company_id}:careers:{observed_at.date()}",
            direction_pressure=pressure_direction, direction_expansion=expansion_direction,
            strength=_strength_from_share(share), source_reliability=0.60, measurement_quality=0.65,
            materiality=min(1.0, count / 5), independence=1.0, raw_value=round(share, 4), unit="share",
            explanation=f"{count} of {total} observed live vacancies matched the {label} taxonomy.",
            extraction_method="deterministic_title_description_taxonomy"))
    return rows

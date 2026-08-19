from __future__ import annotations

import re
from collections import Counter
from datetime import UTC, date, datetime

from evidence_engine_v0_1.models import FeatureSnapshot, JobRecord

FUNCTIONS = {
    "operations": r"operations?|plant|production|warehouse|quality",
    "procurement": r"procurement|purchasing|sourcing|buyer",
    "transformation": r"transformation|change|programme|program manager",
    "finance": r"finance|financial|accountant|treasury",
    "ai_data": r"\bai\b|data|machine learning|analytics",
    "manufacturing": r"manufactur|factory|machinist|engineering",
}


def infer_function(title: str, department: str | None = None) -> str:
    text = f"{title} {department or ''}".lower()
    return next((name for name, pattern in FUNCTIONS.items() if re.search(pattern, text)), "other")


def infer_seniority(title: str) -> str:
    lower = title.lower()
    if re.search(r"chief|director|vice president|\bvp\b|head of", lower):
        return "senior"
    if re.search(r"manager|lead", lower):
        return "manager"
    return "individual_contributor"


def deduplicate_jobs(jobs: list[JobRecord]) -> list[JobRecord]:
    chosen = {}
    for job in sorted(jobs, key=lambda item: item.collected_at):
        existing = chosen.get(job.identity)
        if existing:
            job.first_seen = min(existing.first_seen, job.first_seen)
            job.last_seen = max(existing.last_seen, job.last_seen)
        chosen[job.identity] = job
    return sorted(chosen.values(), key=lambda item: item.identity)


def calculate_job_features(company_id: str, current: list[JobRecord], previous: list[JobRecord],
                           as_of_date: date, current_evidence_id: str | None = None,
                           previous_evidence_id: str | None = None) -> list[FeatureSnapshot]:
    current = [j for j in deduplicate_jobs(current) if j.company_id == company_id and j.status == "open"]
    previous = [j for j in deduplicate_jobs(previous) if j.company_id == company_id and j.status == "open"]
    current_ids, previous_ids = {j.identity for j in current}, {j.identity for j in previous}
    features = {
        "open_vacancy_count": len(current),
        "vacancy_count_change": len(current) - len(previous),
        "vacancy_velocity_new": len(current_ids - previous_ids),
        "closed_vacancies": len(previous_ids - current_ids),
    }
    current_mix = Counter(j.function or infer_function(j.title) for j in current)
    previous_mix = Counter(j.function or infer_function(j.title) for j in previous)
    for function in FUNCTIONS:
        features[f"{function}_hiring_count"] = current_mix[function]
        features[f"{function}_hiring_change"] = current_mix[function] - previous_mix[function]
        features[f"{function}_hiring_share"] = round(current_mix[function] / len(current), 6) if current else None
    features["geographic_hiring_expansion"] = len({j.location for j in current if j.location} - {j.location for j in previous if j.location})
    features["senior_hiring_change"] = sum(j.seniority == "senior" for j in current) - sum(j.seniority == "senior" for j in previous)
    created = datetime.now(UTC)
    evidence_ids = [value for value in (previous_evidence_id, current_evidence_id) if value]
    return [FeatureSnapshot(feature_snapshot_id=f"job-{company_id}-{name}-{as_of_date}",
        company_id=company_id, feature_id=name, feature_version="0.1.0", as_of_date=as_of_date,
        value=value, unit="ratio" if name.endswith("share") else "count",
        calculation="deterministic comparison of deduplicated vacancy snapshots",
        evidence_ids=evidence_ids, quality=1.0, created_at=created)
        for name, value in sorted(features.items())]

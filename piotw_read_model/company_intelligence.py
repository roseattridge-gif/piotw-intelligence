from __future__ import annotations

import hashlib
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

DIMENSIONS = [
    ("demand_growth", "Demand & Growth"),
    ("delivery_capacity", "Delivery & Capacity"),
    ("cost_productivity", "Cost & Productivity"),
    ("cash_working_capital", "Cash & Working Capital"),
    ("workforce_capability", "Workforce & Capability"),
    ("supply_chain_resilience", "Supply Chain & Resilience"),
    ("quality_customer", "Quality & Customer"),
    ("change_execution", "Change & Execution"),
]


class ValidationPlaceholder(BaseModel):
    status: Literal["NOT_YET_VALIDATED"] = "NOT_YET_VALIDATED"
    value: None = None


class Provenance(BaseModel):
    source_family: str
    source_url: str | None
    source_hash: str | None
    observed_at: datetime
    effective_at: datetime | None
    collector_version: str


class FactualObservation(BaseModel):
    observation_id: str
    observation_type: str
    state: int | float | str | None
    change: int | float | None
    velocity: int | float | None
    novelty: bool | None
    persistence: int | None
    unit: str | None
    validation_status: str
    provenance: list[Provenance]


class DimensionView(BaseModel):
    dimension_id: str
    name: str
    coverage_status: str
    observations: list[FactualObservation] = Field(default_factory=list)
    accepted_events: list[dict[str, Any]] = Field(default_factory=list)
    score: ValidationPlaceholder = Field(default_factory=ValidationPlaceholder)


class CareersHistoryPoint(BaseModel):
    observed_at: datetime
    open_roles: int
    new_roles: int
    persistent_roles: int
    absent_once_roles: int
    confirmed_closed_roles: int
    reopened_roles: int
    source_hash: str
    collector_version: str


class CompanyIntelligenceSnapshot(BaseModel):
    schema_version: Literal["company-intelligence-snapshot-v1"]
    company_id: str
    display_name: str
    observation_date: datetime
    dimensions: list[DimensionView]
    source_freshness: list[dict[str, Any]]
    data_coverage: dict[str, Any]
    prediction: ValidationPlaceholder = Field(default_factory=ValidationPlaceholder)
    overall_score: ValidationPlaceholder = Field(default_factory=ValidationPlaceholder)
    benchmark: ValidationPlaceholder = Field(default_factory=ValidationPlaceholder)
    pressure: ValidationPlaceholder = Field(default_factory=ValidationPlaceholder)
    expansion: ValidationPlaceholder = Field(default_factory=ValidationPlaceholder)
    careers_history: list[CareersHistoryPoint] = Field(default_factory=list)


def build_careers_profile(database: str | Path, *, company_id: str, display_name: str,
                          as_of: datetime | None = None) -> CompanyIntelligenceSnapshot:
    as_of = as_of or datetime.now(UTC)
    with sqlite3.connect(database) as connection:
        source = connection.execute("""SELECT provider,last_successful_fetch,next_eligible_fetch,
            consecutive_failures,health FROM career_source_state WHERE company_id=?""", (company_id,)).fetchone()
        snapshots = connection.execute("""SELECT fetch_timestamp,open_count,source_hash,collector_version
            FROM career_collection_snapshots WHERE company_id=? ORDER BY fetch_timestamp""",
            (company_id,)).fetchall()
        if not source or not snapshots:
            raise ValueError(f"no careers evidence for company {company_id}")
        latest, prior = snapshots[-1], snapshots[-2] if len(snapshots) > 1 else None
        new_count = connection.execute("""SELECT count(*) FROM career_job_lifecycle
            WHERE company_id=? AND first_seen=?""", (company_id, latest[0])).fetchone()[0]
        absent = connection.execute("""SELECT count(*) FROM career_job_lifecycle
            WHERE company_id=? AND status='open' AND absent_healthy_runs>0""", (company_id,)).fetchone()[0]
        closed = connection.execute("""SELECT count(*) FROM career_job_lifecycle
            WHERE company_id=? AND status='closed'""", (company_id,)).fetchone()[0]
        reopened = connection.execute("""SELECT COALESCE(sum(reopened_count),0) FROM career_job_lifecycle
            WHERE company_id=?""", (company_id,)).fetchone()[0]
        samples = connection.execute("""SELECT source_url,source_hash FROM career_job_lifecycle
            WHERE company_id=? AND status='open' ORDER BY identity LIMIT 5""", (company_id,)).fetchall()
        lifecycle = connection.execute("""SELECT first_seen,last_seen,status,absent_healthy_runs,reopened_count
            FROM career_job_lifecycle WHERE company_id=?""", (company_id,)).fetchall()
    latest_at = datetime.fromisoformat(latest[0])
    provenance = [Provenance(source_family="careers_ats", source_url=url, source_hash=digest,
        observed_at=latest_at, effective_at=latest_at, collector_version=latest[3]) for url, digest in samples]
    observation_id = hashlib.sha256(f"{company_id}|open_vacancies|{latest[0]}".encode()).hexdigest()[:24]
    movement = FactualObservation(observation_id=observation_id, observation_type="open_vacancies", state=latest[1],
        change=latest[1] - prior[1] if prior else None,
        velocity=(latest[1] - prior[1]) / max((latest_at - datetime.fromisoformat(prior[0])).total_seconds() / 86400, 1)
        if prior else None, novelty=new_count > 0, persistence=2 if prior else 1, unit="postings",
        validation_status="DETERMINISTIC_OBSERVATION_NOT_PREDICTIVE", provenance=provenance)
    dimensions = []
    for dimension_id, name in DIMENSIONS:
        observations = [movement] if dimension_id == "workforce_capability" else []
        dimensions.append(DimensionView(dimension_id=dimension_id, name=name,
            coverage_status="OBSERVED" if observations else "INSUFFICIENT_SOURCE_COVERAGE",
            observations=observations))
    history = []
    previous_open = 0
    for fetch_timestamp, open_count, source_hash, collector_version in snapshots:
        new_roles = sum(1 for first_seen, *_ in lifecycle if first_seen == fetch_timestamp)
        latest_point = fetch_timestamp == latest[0]
        absent_once_roles = sum(1 for _, _, status, absent_runs, _ in lifecycle
            if latest_point and status == "open" and absent_runs == 1)
        confirmed_closed_roles = sum(1 for _, last_seen, status, _, _ in lifecycle
            if status == "closed" and last_seen <= fetch_timestamp)
        reopened_roles = sum(reopened for *_, reopened in lifecycle) if latest_point else 0
        history.append(CareersHistoryPoint(observed_at=datetime.fromisoformat(fetch_timestamp),
            open_roles=open_count, new_roles=new_roles,
            persistent_roles=max(open_count - new_roles, 0) if previous_open else 0,
            absent_once_roles=absent_once_roles, confirmed_closed_roles=confirmed_closed_roles,
            reopened_roles=reopened_roles, source_hash=source_hash, collector_version=collector_version))
        previous_open = open_count
    return CompanyIntelligenceSnapshot(schema_version="company-intelligence-snapshot-v1",
        company_id=company_id, display_name=display_name, observation_date=as_of,
        dimensions=dimensions, source_freshness=[{"source_family": "careers_ats",
            "source_adapter": source[0], "last_successful_fetch": source[1],
            "next_due_collection": source[2], "consecutive_failures": source[3], "health": source[4]},
            {"source_family": "contracts_procurement", "health": "COLLECTING_UNRESOLVED",
             "company_attachment": "NO_APPROVED_ENTITY_MATCH"}],
        data_coverage={"careers_snapshots": len(snapshots), "new": new_count, "absent": absent,
            "closed": closed, "reopened": reopened,
            "procurement_company_records": 0,
            "source_families_missing": ["issuer_reporting"],
            "stale_sources": 0, "failed_sources": 1 if source[4] != "healthy" else 0,
            "coverage_note": "Procurement records are not attached without approved entity resolution."},
        careers_history=history)

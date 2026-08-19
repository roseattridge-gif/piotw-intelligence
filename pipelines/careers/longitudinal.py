from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from pipelines.careers.models import JobPosting

SCHEMA = """
CREATE TABLE IF NOT EXISTS career_source_state (
  company_id TEXT NOT NULL, provider TEXT NOT NULL, desired_cadence_hours INTEGER NOT NULL,
  last_successful_fetch TEXT, next_eligible_fetch TEXT, consecutive_failures INTEGER NOT NULL DEFAULT 0,
  backoff_hours INTEGER NOT NULL DEFAULT 0, health TEXT NOT NULL, last_content_hash TEXT,
  PRIMARY KEY(company_id, provider)
);
CREATE TABLE IF NOT EXISTS career_job_lifecycle (
  identity TEXT PRIMARY KEY, company_id TEXT NOT NULL, provider TEXT NOT NULL, external_id TEXT NOT NULL,
  title TEXT NOT NULL, function_class TEXT, seniority TEXT, location TEXT, source_url TEXT NOT NULL,
  first_seen TEXT NOT NULL, last_seen TEXT NOT NULL, status TEXT NOT NULL, absent_healthy_runs INTEGER NOT NULL,
  reopened_count INTEGER NOT NULL, source_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS career_collection_snapshots (
  snapshot_id TEXT PRIMARY KEY, company_id TEXT NOT NULL, provider TEXT NOT NULL, fetch_timestamp TEXT NOT NULL,
  retrieval_status TEXT NOT NULL, source_hash TEXT, open_count INTEGER NOT NULL, collector_version TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS career_snapshot_roles (
  snapshot_id TEXT NOT NULL, identity TEXT NOT NULL, company_id TEXT NOT NULL, provider TEXT NOT NULL,
  external_id TEXT NOT NULL, title TEXT NOT NULL, department TEXT, raw_location TEXT,
  function_class TEXT NOT NULL, seniority_class TEXT NOT NULL, country TEXT, region TEXT, city TEXT,
  workplace_type TEXT, employment_type TEXT, named_technologies TEXT NOT NULL,
  skill_families TEXT NOT NULL, source_url TEXT NOT NULL, role_hash TEXT NOT NULL,
  derived_origin TEXT NOT NULL, derived_version TEXT NOT NULL,
  PRIMARY KEY(snapshot_id, identity)
);
CREATE TABLE IF NOT EXISTS career_snapshot_aggregates (
  snapshot_id TEXT PRIMARY KEY, schema_version TEXT NOT NULL, derived_version TEXT NOT NULL,
  derived_origin TEXT NOT NULL, total_open INTEGER NOT NULL, new_count INTEGER,
  persistent_count INTEGER, absent_once_count INTEGER, confirmed_closed_count INTEGER,
  reopened_count INTEGER, function_mix TEXT NOT NULL, seniority_mix TEXT NOT NULL,
  geography_mix TEXT NOT NULL, workplace_mix TEXT NOT NULL, technology_mix TEXT NOT NULL,
  missingness TEXT NOT NULL, aggregate_hash TEXT NOT NULL
);
"""

DERIVED_VERSION = "careers-snapshot-features-v0.1"
FUNCTION_CLASSES = ("engineering", "product", "sales", "marketing", "operations", "finance",
                    "hr_people", "legal_compliance", "customer_service", "data_ai", "other_unknown")
SENIORITY_CLASSES = ("individual_contributor", "manager", "director", "vp_executive", "unknown")


def _classify_function(title: str, department: str | None) -> str:
    value = f"{title} {department or ''}".lower()
    padded = f" {value} "
    for label, words in {
        "data_ai": ("data scientist", "data engineer", "machine learning", "artificial intelligence", " ai ", "analytics"),
        "engineering": ("engineer", "developer", "software", "platform", "infrastructure", "security"),
        "product": ("product manager", "product design", "product operations"),
        "sales": ("sales", "account executive", "business development", "revenue"),
        "marketing": ("marketing", "communications", "brand", "content"),
        "finance": ("finance", "financial", "accountant", "accounting", "treasury", "tax"),
        "hr_people": ("human resources", "people operations", "recruit", "talent", "compensation"),
        "legal_compliance": ("legal", "counsel", "compliance", "privacy"),
        "customer_service": ("customer success", "customer support", "service desk", "technical support"),
        "operations": ("operations", "procurement", "sourcing", "supply chain", "manufacturing", "plant", "production"),
    }.items():
        if any(word in padded for word in words):
            return label
    return "other_unknown"


def _seniority(title: str) -> str:
    value = title.lower()
    if any(word in value for word in ("chief ", "chief", "vice president", "vp ", "vp,", "head of", "president")):
        return "vp_executive"
    if "director" in value:
        return "director"
    if any(word in value for word in ("manager", "team lead", "engineering lead", "supervisor")):
        return "manager"
    if title.strip():
        return "individual_contributor"
    return "unknown"


def _geography(location: str | None) -> tuple[str | None, str | None, str | None]:
    if not location:
        return None, None, None
    parts = [part.strip() for part in location.split(",") if part.strip()]
    value = location.lower()
    country = next((name for token, name in {
        "united states": "United States", " usa": "United States", "united kingdom": "United Kingdom",
        " uk": "United Kingdom", "canada": "Canada", "germany": "Germany", "france": "France",
        "ireland": "Ireland", "india": "India", "australia": "Australia", "singapore": "Singapore",
        "japan": "Japan", "netherlands": "Netherlands", "spain": "Spain", "italy": "Italy",
    }.items() if token in f" {value}"), None)
    city = parts[0] if parts and not re.search(
        r"\b(remote|hybrid|multiple|various)\b", parts[0], re.IGNORECASE
    ) else None
    region = parts[-2] if len(parts) >= 3 else None
    return country, region, city


def _technologies(job: JobPosting) -> tuple[list[str], list[str]]:
    # v0.1 deliberately uses title/department only. Long boilerplate descriptions often name
    # the employer's whole platform or competitors and would overstate role-specific skills.
    text = " ".join(filter(None, (job.title, job.department))).lower()
    aliases = {
        "Python": ("python",), "Java": ("java",), "SQL": (" sql", "sql "),
        "AWS": ("aws", "amazon web services"), "Azure": ("azure",), "GCP": ("gcp", "google cloud"),
        "Kubernetes": ("kubernetes",), "Snowflake": ("snowflake",), "Databricks": ("databricks",),
        "SAP": (" sap", "sap "), "Oracle": ("oracle",), "Salesforce": ("salesforce",),
        "Workday": ("workday",), "AI/ML": ("machine learning", "artificial intelligence", " ai ", " ml "),
    }
    named = sorted(name for name, terms in aliases.items() if any(term in f" {text} " for term in terms))
    families = []
    if any(name in named for name in ("Python", "Java", "SQL")): families.append("software_data_languages")
    if any(name in named for name in ("AWS", "Azure", "GCP", "Kubernetes")): families.append("cloud_platforms")
    if any(name in named for name in ("Snowflake", "Databricks", "AI/ML")): families.append("data_ai")
    if any(name in named for name in ("SAP", "Oracle", "Salesforce", "Workday")): families.append("enterprise_applications")
    return named, families


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _snapshot_feature_payload(jobs: list[JobPosting]) -> tuple[list[tuple[object, ...]], dict[str, object]]:
    roles: list[tuple[object, ...]] = []
    functions: Counter[str] = Counter(); seniority: Counter[str] = Counter()
    countries: Counter[str] = Counter(); workplaces: Counter[str] = Counter(); technologies: Counter[str] = Counter()
    missing = Counter()
    for job in jobs:
        function = _classify_function(job.title, job.department); level = _seniority(job.title)
        country, region, city = _geography(job.location); named, families = _technologies(job)
        functions[function] += 1; seniority[level] += 1
        countries[country or "unknown"] += 1; workplaces[job.workplace_type or "unknown"] += 1
        technologies.update(named)
        for field, value in (("department", job.department), ("location", job.location),
                             ("workplace_type", job.workplace_type), ("employment_type", job.employment_type),
                             ("description", job.description)):
            if not value: missing[field] += 1
        role_hash = hashlib.sha256(_json(job.model_dump(mode="json")).encode()).hexdigest()
        roles.append((job.identity, job.company_id, job.provider, job.external_id, job.title, job.department,
            job.location, function, level, country, region, city, job.workplace_type, job.employment_type,
            _json(named), _json(families), job.source_url, role_hash))
    return roles, {"function_mix": dict(functions), "seniority_mix": dict(seniority),
        "geography_mix": dict(countries), "workplace_mix": dict(workplaces),
        "technology_mix": dict(technologies), "missingness": dict(missing)}


def source_is_due(path: str | Path, *, company_id: str, provider: str, as_of: datetime) -> bool:
    if as_of.tzinfo is None: as_of = as_of.replace(tzinfo=UTC)
    if not Path(path).is_file(): return True
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)
        row = connection.execute("SELECT next_eligible_fetch FROM career_source_state WHERE company_id=? AND provider=?",
                                 (company_id, provider)).fetchone()
    return not row or not row[0] or as_of >= datetime.fromisoformat(row[0])


def _source_hash(jobs: list[JobPosting]) -> str:
    material = [{"identity": job.identity, "title": job.title, "location": job.location, "url": job.source_url}
                for job in sorted(jobs, key=lambda row: row.identity)]
    return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class SnapshotResult:
    snapshot_id: str
    open_count: int
    new_count: int
    persistent_count: int
    closed_count: int
    reopened_count: int
    absent_once_count: int
    health: str
    next_eligible_fetch: str


def source_health_report(path: str | Path, *, as_of: datetime) -> list[dict[str, object]]:
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=UTC)
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)
        states = connection.execute("""SELECT company_id,provider,desired_cadence_hours,
            last_successful_fetch,next_eligible_fetch,consecutive_failures,backoff_hours,health
            FROM career_source_state ORDER BY company_id,provider""").fetchall()
        report = []
        for row in states:
            latest = connection.execute("""SELECT open_count FROM career_collection_snapshots
                WHERE company_id=? AND provider=? ORDER BY fetch_timestamp DESC LIMIT 2""",
                (row[0], row[1])).fetchall()
            delta = latest[0][0] - latest[1][0] if len(latest) == 2 else None
            next_due = datetime.fromisoformat(row[4]) if row[4] else None
            report.append({"company_id": row[0], "source_adapter": row[1],
                "expected_cadence_hours": row[2], "last_successful_fetch": row[3],
                "next_due_collection": row[4], "consecutive_failure_count": row[5],
                "backoff_hours": row[6], "health": row[7], "posting_count_delta": delta,
                "anomaly_flag": row[7] == "suspicious_drop",
                "stale_source_flag": bool(next_due and as_of > next_due)})
        return report


def record_snapshot(path: str | Path, *, company_id: str, provider: str, jobs: list[JobPosting],
                    fetched_at: datetime, retrieval_success: bool, desired_cadence_hours: int = 48,
                    closure_confirmation_runs: int = 2, suspicious_drop_ratio: float = 0.8) -> SnapshotResult:
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=UTC)
    database = Path(path); database.parent.mkdir(parents=True, exist_ok=True)
    content_hash = _source_hash(jobs) if retrieval_success else None
    stamp = fetched_at.isoformat()
    snapshot_id = hashlib.sha256(f"{company_id}|{provider}|{stamp}".encode()).hexdigest()[:24]
    with sqlite3.connect(database) as connection:
        connection.executescript(SCHEMA)
        previous = {row[0]: row for row in connection.execute(
            "SELECT identity, status, absent_healthy_runs, reopened_count FROM career_job_lifecycle WHERE company_id=? AND provider=?",
            (company_id, provider))}
        prior_open = sum(row[1] == "open" for row in previous.values())
        suspicious = bool(retrieval_success and prior_open >= 10 and len(jobs) <= prior_open * (1 - suspicious_drop_ratio))
        healthy = retrieval_success and not suspicious
        health = "healthy" if healthy else "suspicious_drop" if retrieval_success else "fetch_failed"
        observed = {job.identity: job for job in jobs}
        new_count = persistent = reopened = closed = absent_once = 0
        if healthy:
            for job in jobs:
                old = previous.get(job.identity)
                if old is None: new_count += 1
                elif old[1] == "closed": reopened += 1
                else: persistent += 1
                connection.execute("""
                  INSERT INTO career_job_lifecycle VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                  ON CONFLICT(identity) DO UPDATE SET title=excluded.title, function_class=excluded.function_class,
                    seniority=excluded.seniority, location=excluded.location, source_url=excluded.source_url,
                    last_seen=excluded.last_seen, status='open', absent_healthy_runs=0,
                    reopened_count=career_job_lifecycle.reopened_count + CASE WHEN career_job_lifecycle.status='closed' THEN 1 ELSE 0 END,
                    source_hash=excluded.source_hash
                """, (job.identity, company_id, provider, job.external_id, job.title,
                    _classify_function(job.title, job.department), _seniority(job.title), job.location,
                    job.source_url, stamp, stamp, "open", 0, (old[3] if old else 0),
                    hashlib.sha256(json.dumps(job.model_dump(mode="json"), sort_keys=True, default=str).encode()).hexdigest()))
            for identity, old in previous.items():
                if old[1] == "open" and identity not in observed:
                    misses = old[2] + 1
                    status = "closed" if misses >= closure_confirmation_runs else "open"
                    closed += status == "closed"
                    absent_once += status == "open"
                    connection.execute("UPDATE career_job_lifecycle SET absent_healthy_runs=?, status=? WHERE identity=?",
                                       (misses, status, identity))
        failures = connection.execute(
            "SELECT consecutive_failures FROM career_source_state WHERE company_id=? AND provider=?",
            (company_id, provider)).fetchone()
        failure_count = 0 if healthy else (failures[0] if failures else 0) + 1
        backoff = min(24 * (2 ** max(failure_count - 1, 0)), 168) if not healthy else 0
        next_at = fetched_at + timedelta(hours=max(desired_cadence_hours, backoff))
        connection.execute("""INSERT INTO career_source_state VALUES(?,?,?,?,?,?,?,?,?)
          ON CONFLICT(company_id,provider) DO UPDATE SET desired_cadence_hours=excluded.desired_cadence_hours,
          last_successful_fetch=COALESCE(excluded.last_successful_fetch,career_source_state.last_successful_fetch),
          next_eligible_fetch=excluded.next_eligible_fetch, consecutive_failures=excluded.consecutive_failures,
          backoff_hours=excluded.backoff_hours, health=excluded.health,
          last_content_hash=COALESCE(excluded.last_content_hash,career_source_state.last_content_hash)""",
          (company_id, provider, desired_cadence_hours, stamp if healthy else None, next_at.isoformat(),
           failure_count, backoff, health, content_hash))
        connection.execute("INSERT OR REPLACE INTO career_collection_snapshots VALUES(?,?,?,?,?,?,?,?)",
            (snapshot_id, company_id, provider, stamp, health, content_hash, len(jobs), "careers-longitudinal-v1"))
        if healthy:
            roles, derived = _snapshot_feature_payload(jobs)
            connection.execute("DELETE FROM career_snapshot_roles WHERE snapshot_id=?", (snapshot_id,))
            connection.executemany("""INSERT INTO career_snapshot_roles VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                [(snapshot_id, *role, "LIVE_COLLECTION", DERIVED_VERSION) for role in roles])
            aggregate = {"total_open": len(jobs), "new_count": new_count, "persistent_count": persistent,
                "absent_once_count": absent_once, "confirmed_closed_count": closed, "reopened_count": reopened, **derived}
            aggregate_hash = hashlib.sha256(_json(aggregate).encode()).hexdigest()
            connection.execute("""INSERT OR REPLACE INTO career_snapshot_aggregates VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (snapshot_id, "piotw-careers-snapshot-v0.1", DERIVED_VERSION, "LIVE_COLLECTION", len(jobs),
                 new_count, persistent, absent_once, closed, reopened, _json(derived["function_mix"]),
                 _json(derived["seniority_mix"]), _json(derived["geography_mix"]),
                 _json(derived["workplace_mix"]), _json(derived["technology_mix"]),
                 _json(derived["missingness"]), aggregate_hash))
    return SnapshotResult(snapshot_id, len(jobs), new_count, persistent, closed, reopened, absent_once,
                          health, next_at.isoformat())

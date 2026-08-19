from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from evidence_engine_v0_1.models import (
    Event,
    FeatureDefinition,
    FeatureSnapshot,
    Observation,
    RawEvidence,
    ReviewDecision,
)


class EvidenceStore:
    def __init__(self, database: str | Path, raw_root: str | Path):
        self.database = Path(database)
        self.raw_root = Path(raw_root)

    def initialize(self, schema: str | Path) -> None:
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database) as connection:
            connection.executescript(Path(schema).read_text())

    def persist_raw(self, evidence: RawEvidence) -> None:
        path = self.raw_root / evidence.company_id / f"{evidence.evidence_id}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(evidence.raw_text)
        source_id = f"src-{evidence.evidence_id}"
        with sqlite3.connect(self.database) as c:
            c.execute("INSERT OR IGNORE INTO ee01_companies VALUES(?,?)", (evidence.company_id, evidence.company_id))
            c.execute("INSERT OR IGNORE INTO ee01_sources VALUES(?,?,?,?)", (source_id, evidence.source_type, evidence.source_title, evidence.source_url))
            c.execute("INSERT OR REPLACE INTO ee01_raw_evidence VALUES(?,?,?,?,?,?,?,?,?,?,?)", (
                evidence.evidence_id, evidence.company_id, source_id, evidence.reporting_period,
                evidence.publication_date.isoformat(), evidence.observation_date.isoformat() if evidence.observation_date else None,
                evidence.collected_at.isoformat(), evidence.information_available_at.isoformat(), evidence.content_hash,
                str(path), evidence.collector_version))

    def persist_observation(self, obs: Observation) -> None:
        with sqlite3.connect(self.database) as c:
            c.execute("INSERT OR REPLACE INTO ee01_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                obs.observation_id, obs.company_id, obs.observation_type, obs.reporting_period,
                json.dumps(obs.value), obs.unit, obs.currency, obs.source_evidence_id, obs.evidence_span,
                obs.page_or_section, obs.publication_date.isoformat(), obs.observation_date.isoformat() if obs.observation_date else None,
                obs.information_available_at.isoformat(), obs.extraction_confidence, obs.parser_version,
                obs.extraction_method, obs.llm_model, obs.prompt_version, obs.extracted_at.isoformat(),
                obs.validation_status, int(obs.quantified), json.dumps(obs.metadata, sort_keys=True)))

    def persist_review(self, decision: ReviewDecision) -> None:
        with sqlite3.connect(self.database) as c:
            c.execute("INSERT INTO ee01_review_decisions VALUES(?,?,?,?,?,?,?,?)", (
                decision.decision_id, decision.observation_id, decision.decision, decision.reviewer,
                decision.decided_at.isoformat(), json.dumps(decision.corrected_value), decision.corrected_unit, decision.note))

    def persist_event(self, event: Event, observations: dict[str, Observation]) -> None:
        with sqlite3.connect(self.database) as c:
            c.execute("INSERT OR REPLACE INTO ee01_events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                event.event_id, event.company_id, event.event_type, event.taxonomy_group, event.reporting_period,
                event.event_date.isoformat(), event.information_available_at.isoformat(), event.evidence_span,
                int(event.quantified), event.severity, event.novelty, event.extraction_confidence, event.taxonomy_version))
            for observation_id in event.source_observation_ids:
                obs = observations[observation_id]
                c.execute("INSERT OR IGNORE INTO ee01_event_evidence VALUES(?,?,?)",
                          (event.event_id, observation_id, obs.source_evidence_id))

    def persist_feature(self, feature: FeatureSnapshot) -> None:
        with sqlite3.connect(self.database) as c:
            c.execute("INSERT OR REPLACE INTO ee01_feature_snapshots VALUES(?,?,?,?,?,?,?,?,?,?)", (
                feature.feature_snapshot_id, feature.company_id, feature.feature_id, feature.feature_version,
                feature.as_of_date.isoformat(), json.dumps(feature.value), feature.unit, feature.calculation,
                feature.quality, feature.created_at.isoformat()))
            c.execute("DELETE FROM ee01_feature_provenance WHERE snapshot_id=?", (feature.feature_snapshot_id,))
            rows = max(len(feature.input_observation_ids), len(feature.input_event_ids), len(feature.evidence_ids), 1)
            for index in range(rows):
                c.execute("INSERT INTO ee01_feature_provenance VALUES(?,?,?,?)", (
                    feature.feature_snapshot_id,
                    feature.input_observation_ids[index] if index < len(feature.input_observation_ids) else None,
                    feature.input_event_ids[index] if index < len(feature.input_event_ids) else None,
                    feature.evidence_ids[index] if index < len(feature.evidence_ids) else None))

    def persist_feature_definition(self, definition: FeatureDefinition) -> None:
        with sqlite3.connect(self.database) as c:
            c.execute("INSERT OR REPLACE INTO ee01_feature_definitions VALUES(?,?,?,?)", (
                definition.feature_id, definition.version, definition.model_dump_json(),
                definition.effective_from.isoformat()))

    def persist_job(self, job) -> None:
        with sqlite3.connect(self.database) as c:
            c.execute("INSERT OR REPLACE INTO ee01_jobs VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (
                job.identity, job.company_id, job.posting_id, job.title, job.function, job.seniority,
                job.location, job.source_url, job.collected_at.isoformat(), job.first_seen.isoformat(),
                job.last_seen.isoformat(), job.status))

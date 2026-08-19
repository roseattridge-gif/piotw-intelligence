from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path

import yaml

from evidence_engine_v0_1.models import Event, Observation, RawEvidence


def load_taxonomy(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text())


def extract_language_observations(evidence: RawEvidence, taxonomy: dict) -> list[Observation]:
    output = []
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", evidence.raw_text) if s.strip()]
    for index, sentence in enumerate(sentences):
        lower = sentence.lower()
        for group, definitions in taxonomy["groups"].items():
            for event_type, definition in definitions.items():
                if not any(re.search(pattern, lower, re.IGNORECASE) for pattern in definition["patterns"]):
                    continue
                quantified = bool(re.search(r"\b\d+(?:\.\d+)?\s*(?:%|percent|£|\$|€|m|million|bn|billion|roles|jobs)\b", sentence, re.IGNORECASE))
                identity = hashlib.sha256(f"{evidence.evidence_id}|{index}|{event_type}|{sentence}".encode()).hexdigest()[:16]
                output.append(Observation(
                    observation_id=f"obs-{identity}", company_id=evidence.company_id,
                    observation_type=event_type, reporting_period=evidence.reporting_period,
                    value=True, unit="occurrence", source_evidence_id=evidence.evidence_id,
                    evidence_span=sentence, page_or_section=f"sentence {index + 1}",
                    publication_date=evidence.publication_date, observation_date=evidence.observation_date,
                    information_available_at=evidence.information_available_at,
                    extraction_confidence=float(definition.get("deterministic_confidence", .85)),
                    parser_version=f"taxonomy-{taxonomy['version']}", extraction_method="deterministic",
                    extracted_at=datetime.now(UTC), quantified=quantified,
                    metadata={"taxonomy_group": group},
                ))
    return output


def observations_to_events(observations: list[Observation], taxonomy: dict) -> list[Event]:
    seen: dict[tuple[str, str, str, str], Event] = {}
    for obs in observations:
        group = obs.metadata.get("taxonomy_group")
        if not group or obs.validation_status == "rejected":
            continue
        normalized = re.sub(r"\W+", " ", obs.evidence_span.lower()).strip()
        key = (obs.company_id, obs.observation_type, obs.reporting_period, normalized)
        if key in seen:
            ids = seen[key].source_observation_ids
            if obs.observation_id not in ids:
                ids.append(obs.observation_id)
            continue
        fingerprint = hashlib.sha256("|".join(key).encode()).hexdigest()[:16]
        seen[key] = Event(
            event_id=f"evt-{fingerprint}", company_id=obs.company_id,
            event_type=obs.observation_type, taxonomy_group=group,
            reporting_period=obs.reporting_period,
            event_date=obs.observation_date or obs.publication_date,
            information_available_at=obs.information_available_at,
            evidence_span=obs.evidence_span, quantified=obs.quantified,
            extraction_confidence=obs.extraction_confidence,
            taxonomy_version=taxonomy["version"], source_observation_ids=[obs.observation_id],
        )
    ordered = sorted(seen.values(), key=lambda event: (event.company_id, event.event_type, event.reporting_period, event.event_id))
    histories: dict[tuple[str, str], int] = {}
    for event in ordered:
        history_key = (event.company_id, event.event_type)
        event.novelty = "new" if history_key not in histories else "persistent"
        histories[history_key] = histories.get(history_key, 0) + 1
    return ordered


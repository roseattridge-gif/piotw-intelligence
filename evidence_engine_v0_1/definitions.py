from __future__ import annotations

from datetime import date

from evidence_engine_v0_1.features import NUMERIC_FEATURES
from evidence_engine_v0_1.jobs import FUNCTIONS
from evidence_engine_v0_1.models import FeatureDefinition


def feature_definition_catalog(taxonomy: dict) -> list[FeatureDefinition]:
    definitions = []
    for observation_type, (feature_id, unit, method) in NUMERIC_FEATURES.items():
        definitions.append(FeatureDefinition(
            feature_id=feature_id, name=feature_id.replace("_", " "), version="0.1.0",
            definition=f"Change in comparable {observation_type} across the latest two eligible periods",
            required_observation_types=[observation_type], calculation=method, unit=unit,
            missing_data="null", lookback_periods=2, effective_from=date(2026, 8, 15)))
    for group in taxonomy["groups"].values():
        for event_type in group:
            for suffix, definition, unit in [
                ("count", "Count in latest eligible reporting period", "count"),
                ("mentions_change", "Latest event count minus prior-period count", "count"),
                ("new_flag", "One when event is absent in prior period", "boolean"),
                ("persistence_periods", "Number of eligible periods containing event", "periods"),
            ]:
                definitions.append(FeatureDefinition(
                    feature_id=f"{event_type}_{suffix}", name=f"{event_type} {suffix}".replace("_", " "),
                    version="0.1.0", definition=definition,
                    required_observation_types=[event_type], calculation=suffix, unit=unit,
                    missing_data="null", lookback_periods=2, effective_from=date(2026, 8, 15)))
    job_ids = ["open_vacancy_count", "vacancy_count_change", "vacancy_velocity_new",
               "closed_vacancies", "geographic_hiring_expansion", "senior_hiring_change"]
    for function in FUNCTIONS:
        job_ids.extend([f"{function}_hiring_count", f"{function}_hiring_change",
                        f"{function}_hiring_share"])
    for feature_id in job_ids:
        definitions.append(FeatureDefinition(
            feature_id=feature_id, name=feature_id.replace("_", " "), version="0.1.0",
            definition="Deterministic comparison of deduplicated careers snapshots",
            required_observation_types=["job_posting"], calculation=feature_id,
            unit="ratio" if feature_id.endswith("share") else "count", missing_data="null",
            lookback_periods=2, effective_from=date(2026, 8, 15)))
    return definitions

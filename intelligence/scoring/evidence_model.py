from __future__ import annotations

import math
from collections import defaultdict
from datetime import date, datetime, time, timezone
from pathlib import Path

from intelligence.models import (
    EvidenceContribution,
    EvidenceObservation,
    ModelPrediction,
    SourceCoverage,
)


def _scalar(value: str) -> object:
    value = value.strip()
    if value.startswith("{") and value.endswith("}"):
        result = {}
        for pair in value[1:-1].split(","):
            if pair.strip():
                key, item = pair.split(":", 1)
                result[key.strip()] = _scalar(item)
        return result
    if value in {"true", "false"}:
        return value == "true"
    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value.strip("\"'")


def _load_simple_yaml(path: str | Path) -> dict:
    """Load the deliberately simple mapping-only ontology without a runtime dependency."""
    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]
    for source_line in Path(path).read_text().splitlines():
        line = source_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        key, value = line.strip().split(":", 1)
        while stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if value.strip():
            parent[key] = _scalar(value)
        else:
            parent[key] = {}
            stack.append((indent, parent[key]))
    return root


class EvidenceModel:
    """Transparent v0.2 prior model. No LLM selects or changes the score."""

    version = "evidence-model-0.2.0"

    def __init__(self, weights_path: str | Path, catalog_path: str | Path,
                 evidence_scale: float = 5.0):
        self.weights = _load_simple_yaml(weights_path)
        self.catalog = _load_simple_yaml(catalog_path)
        self.evidence_scale = evidence_scale

    @property
    def families(self) -> set[str]:
        return set(self.weights["models"]["operational_pressure"])

    def _half_life(self, observation: EvidenceObservation) -> int:
        feature = (self.catalog.get("families", {}).get(observation.family, {})
                   .get("features", {}).get(observation.feature, {}))
        if "half_life_days" in feature:
            return int(feature["half_life_days"])
        fallbacks = self.weights.get("recency_half_life_days", {})
        return int(fallbacks.get(observation.feature, 365))

    def predict(self, company_id: str, model: str, horizon_months: int, as_of_date: date,
                observations: list[EvidenceObservation], coverage: list[SourceCoverage],
                prior_probability: float = 0.20) -> ModelPrediction:
        if model not in self.weights["models"]:
            raise ValueError(f"Unknown model: {model}")
        if horizon_months not in {6, 12, 18}:
            raise ValueError("Horizon must be 6, 12 or 18 months")

        cutoff = datetime.combine(as_of_date, time.max, tzinfo=timezone.utc)
        eligible = [o for o in observations if o.company_id == company_id and o.available_at <= cutoff]
        family_weights = self.weights["models"][model]
        raw_by_cluster: dict[str, list[tuple[EvidenceObservation, float]]] = defaultdict(list)
        direction_field = "direction_pressure" if model == "operational_pressure" else "direction_expansion"
        relevance_field = "relevance_pressure" if model == "operational_pressure" else "relevance_expansion"

        for item in eligible:
            if item.family not in family_weights:
                continue
            age_days = max(0, (as_of_date - item.event_date).days)
            recency = math.exp(-math.log(2) * age_days / self._half_life(item))
            contribution = (
                family_weights[item.family]
                * item.strength
                * item.source_reliability
                * item.measurement_quality
                * item.materiality
                * recency
                * item.independence
                * getattr(item, relevance_field)
                * getattr(item, direction_field)
            )
            raw_by_cluster[item.event_cluster_id].append((item, contribution))

        contributions: list[EvidenceContribution] = []
        cluster_cap = float(self.weights.get("cluster_contribution_cap", 0.20))
        for cluster_rows in raw_by_cluster.values():
            cluster_total = sum(value for _, value in cluster_rows)
            scale = min(1.0, cluster_cap / abs(cluster_total)) if cluster_total else 1.0
            for item, value in cluster_rows:
                contributions.append(EvidenceContribution(
                    observation_id=item.observation_id,
                    event_cluster_id=item.event_cluster_id,
                    family=item.family,
                    feature=item.feature,
                    contribution=round(value * scale, 8),
                    explanation=item.explanation,
                    source_url=item.source_url,
                ))

        evidence_sum = sum(item.contribution for item in contributions)
        prior_logit = math.log(prior_probability / (1 - prior_probability))
        probability = 1 / (1 + math.exp(-(prior_logit + self.evidence_scale * evidence_sum)))

        coverage_by_family = {row.family: row.coverage for row in coverage
                              if row.company_id == company_id and row.as_of_date <= as_of_date}
        coverage_score = sum(family_weights[f] * coverage_by_family.get(f, 0) for f in family_weights)
        missing = sorted(f for f in family_weights if coverage_by_family.get(f, 0) == 0)
        clusters = {item.event_cluster_id for item in eligible}
        mean_quality = (sum(item.measurement_quality * item.source_reliability for item in eligible)
                        / len(eligible) if eligible else 0)
        confidence = coverage_score * mean_quality * (1 - math.exp(-len(clusters) / 3))
        if len(clusters) < 2:
            confidence = min(confidence, float(self.weights["confidence_caps"]["single_evidence_cluster"]))
        if eligible and all(item.source_is_company_controlled for item in eligible):
            confidence = min(confidence, float(self.weights["confidence_caps"]["no_non_company_source"]))

        return ModelPrediction(
            company_id=company_id,
            model=model,
            horizon_months=horizon_months,
            as_of_date=as_of_date,
            probability=round(probability, 6),
            confidence=round(min(1.0, confidence), 6),
            prior_probability=prior_probability,
            evidence_sum=round(evidence_sum, 8),
            coverage=round(coverage_score, 6),
            contributions=sorted(contributions, key=lambda row: abs(row.contribution), reverse=True),
            missing_families=missing,
            model_version=self.version,
        )

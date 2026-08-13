from datetime import date, datetime, timezone

from intelligence.models import EvidenceObservation, SourceCoverage
from intelligence.scoring.evidence_model import EvidenceModel


def observation(direction=1, available="2021-01-01"):
    return EvidenceObservation(
        observation_id="o1", company_id="acme", family="workforce_demand_skills",
        feature="vacancy_acceleration", event_date=date(2021, 1, 1),
        available_at=datetime.fromisoformat(available).replace(tzinfo=timezone.utc),
        source_type="ats", source_url="https://example.test/jobs", source_name="Careers",
        source_is_company_controlled=True, event_cluster_id="cluster-1",
        direction_pressure=direction, direction_expansion=direction, strength=1,
        source_reliability=1, measurement_quality=1, materiality=1, independence=1,
        explanation="Vacancies accelerated", extraction_method="test",
    )


def scorer():
    return EvidenceModel("intelligence/ontology/signal_weights_v02.yaml",
                         "intelligence/ontology/signal_catalog_v02.yaml")


def test_support_increases_and_contradiction_reduces_probability():
    coverage = [SourceCoverage(company_id="acme", family="workforce_demand_skills",
                               as_of_date=date(2021, 12, 31), coverage=1, note="test")]
    positive = scorer().predict("acme", "operational_pressure", 18, date(2021, 12, 31),
                                [observation(1)], coverage)
    negative = scorer().predict("acme", "operational_pressure", 18, date(2021, 12, 31),
                                [observation(-1)], coverage)
    assert positive.probability > 0.2
    assert negative.probability < 0.2
    assert positive.confidence <= 0.55


def test_future_evidence_is_excluded():
    result = scorer().predict("acme", "operational_pressure", 18, date(2021, 12, 31),
                              [observation(1, "2022-01-01")], [])
    assert result.probability == 0.2
    assert not result.contributions

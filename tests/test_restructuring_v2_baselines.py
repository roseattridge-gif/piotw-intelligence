from validation.restructuring_v2 import baseline_probabilities

DEVELOPMENT = [
    {"company": "A", "status": "positive", "occurred": 1},
    {"company": "A", "status": "negative", "occurred": 0},
    {"company": "B", "status": "negative", "occurred": 0},
]


def test_all_frozen_baselines_are_deterministic_and_loco_excludes_company():
    features = {"margin_pressure": 0.7, "cash_pressure": 0.7}
    scores = baseline_probabilities(features, "new restructuring programme", "A", DEVELOPMENT)
    assert scores["constant_prior"] == 0.12
    assert scores["leave_one_company_out_development_rate"] == 0
    assert scores["financial_stress_rule"] == 0.6
    assert scores["disclosure_language_rule"] == 0.2
    assert 0 <= scores["financial_only_logistic"] <= 1


def test_language_exclusion_context_does_not_trigger():
    features = {"margin_pressure": 0.2, "cash_pressure": 0.2}
    scores = baseline_probabilities(features, "previously announced restructuring completed", "C", DEVELOPMENT)
    assert scores["disclosure_language_rule"] == 0.12

from validation.metrics_v2 import (
    brier,
    calibration_table,
    clustered_bootstrap,
    tie_aware_top_group,
)


def test_brier_and_calibration_are_exact():
    probabilities = [0.1, 0.2, 0.8, 0.9]
    outcomes = [0, 1, 1, 1]
    assert brier(probabilities, outcomes) == (0.01 + 0.64 + 0.04 + 0.01) / 4
    table = calibration_table(probabilities, outcomes, [0, 0.5, 1.0000001])
    assert table[0]["n"] == 2 and table[0]["positive_count"] == 1
    assert table[1]["n"] == 2 and table[1]["positive_count"] == 2


def test_top_group_includes_all_boundary_ties():
    result = tie_aware_top_group([0.9, 0.8, 0.8, 0.1, 0.1], [1, 0, 1, 0, 0], 0.4)
    assert result["n"] == 3
    assert result["positive_count"] == 2


def test_clustered_bootstrap_is_reproducible_and_resamples_companies():
    rows = [
        {"stable_id": "a", "probability": 0.8, "outcome": 1, "constant_prior": 0.12},
        {"stable_id": "a", "probability": 0.4, "outcome": 0, "constant_prior": 0.12},
        {"stable_id": "b", "probability": 0.2, "outcome": 0, "constant_prior": 0.12},
        {"stable_id": "c", "probability": 0.6, "outcome": 1, "constant_prior": 0.12},
    ]
    first = clustered_bootstrap(rows, replicates=50, seed=7)
    second = clustered_bootstrap(rows, replicates=50, seed=7)
    assert first == second
    assert first["replicates"] == 50
    assert "brier_difference_vs_prior" in first

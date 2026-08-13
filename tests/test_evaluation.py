from backtesting.evaluation import evaluate_binary


def test_perfect_ranking_has_perfect_average_precision():
    result = evaluate_binary([0.9, 0.8, 0.2, 0.1], [1, 1, 0, 0])
    assert result.average_precision == 1
    assert result.brier_score == 0.025
    assert result.precision == 1
    assert result.recall == 1


def test_rejects_invalid_inputs():
    try:
        evaluate_binary([1.2], [1])
    except ValueError:
        pass
    else:
        raise AssertionError("invalid probability was accepted")

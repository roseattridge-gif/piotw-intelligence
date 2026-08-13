from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BinaryEvaluation:
    n: int
    prevalence: float
    brier_score: float
    precision: float
    recall: float
    average_precision: float
    roc_auc: float | None
    top_quintile_lift: float
    false_positives: int
    false_negatives: int
    calibration: list[dict[str, float | int]]


def evaluate_binary(probabilities: list[float], outcomes: list[int], threshold: float = 0.5,
                    calibration_bins: int = 5) -> BinaryEvaluation:
    if len(probabilities) != len(outcomes) or not outcomes:
        raise ValueError("Probabilities and non-empty outcomes must have equal length")
    if any(not 0 <= value <= 1 for value in probabilities) or any(value not in {0, 1} for value in outcomes):
        raise ValueError("Probabilities must be 0..1 and outcomes binary")
    n = len(outcomes)
    prevalence = sum(outcomes) / n
    brier = sum((probability - outcome) ** 2 for probability, outcome in zip(probabilities, outcomes)) / n
    predicted = [probability >= threshold for probability in probabilities]
    tp = sum(flag and outcome == 1 for flag, outcome in zip(predicted, outcomes))
    fp = sum(flag and outcome == 0 for flag, outcome in zip(predicted, outcomes))
    fn = sum(not flag and outcome == 1 for flag, outcome in zip(predicted, outcomes))
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0

    ranked = sorted(zip(probabilities, outcomes), reverse=True)
    positives = sum(outcomes)
    running_tp = 0
    ap = 0.0
    for rank, (_, outcome) in enumerate(ranked, start=1):
        if outcome:
            running_tp += 1
            ap += running_tp / rank
    average_precision = ap / positives if positives else 0
    positive_scores = [p for p, y in zip(probabilities, outcomes) if y == 1]
    negative_scores = [p for p, y in zip(probabilities, outcomes) if y == 0]
    if positive_scores and negative_scores:
        pair_scores = [1 if positive > negative else 0.5 if positive == negative else 0
                       for positive in positive_scores for negative in negative_scores]
        roc_auc = sum(pair_scores) / len(pair_scores)
    else:
        roc_auc = None
    top_n = max(1, (n + 4) // 5)
    top_rate = sum(outcome for _, outcome in ranked[:top_n]) / top_n
    lift = top_rate / prevalence if prevalence else 0

    bins = []
    for index in range(calibration_bins):
        low, high = index / calibration_bins, (index + 1) / calibration_bins
        members = [(p, y) for p, y in zip(probabilities, outcomes)
                   if low <= p < high or index == calibration_bins - 1 and p == 1]
        if members:
            bins.append({"lower": low, "upper": high, "n": len(members),
                         "mean_probability": sum(p for p, _ in members) / len(members),
                         "observed_rate": sum(y for _, y in members) / len(members)})
    return BinaryEvaluation(n=n, prevalence=round(prevalence, 6), brier_score=round(brier, 6),
                            precision=round(precision, 6), recall=round(recall, 6),
                            average_precision=round(average_precision, 6),
                            roc_auc=round(roc_auc, 6) if roc_auc is not None else None,
                            top_quintile_lift=round(lift, 6), false_positives=fp,
                            false_negatives=fn, calibration=bins)

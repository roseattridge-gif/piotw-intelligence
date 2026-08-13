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

    ranked = sorted(zip(probabilities, outcomes), key=lambda pair: pair[0], reverse=True)
    positives = sum(outcomes)
    # Threshold-group integration makes tied scores order-independent. In
    # particular, a constant score must have AP equal to prevalence.
    running_tp = 0
    running_n = 0
    previous_recall = 0.0
    ap = 0.0
    for score in sorted(set(probabilities), reverse=True):
        group = [(p, y) for p, y in ranked if p == score]
        running_tp += sum(y for _, y in group)
        running_n += len(group)
        recall_at_threshold = running_tp / positives if positives else 0.0
        precision_at_threshold = running_tp / running_n
        ap += (recall_at_threshold - previous_recall) * precision_at_threshold
        previous_recall = recall_at_threshold
    average_precision = ap if positives else 0
    positive_scores = [p for p, y in zip(probabilities, outcomes) if y == 1]
    negative_scores = [p for p, y in zip(probabilities, outcomes) if y == 0]
    if positive_scores and negative_scores:
        pair_scores = [1 if positive > negative else 0.5 if positive == negative else 0
                       for positive in positive_scores for negative in negative_scores]
        roc_auc = sum(pair_scores) / len(pair_scores)
    else:
        roc_auc = None
    top_n = max(1, (n + 4) // 5)
    boundary_score = ranked[top_n - 1][0]
    top_group = [(score, outcome) for score, outcome in ranked if score >= boundary_score]
    top_rate = sum(outcome for _, outcome in top_group) / len(top_group)
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

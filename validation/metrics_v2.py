from __future__ import annotations

import math
import random
import statistics
from collections import defaultdict
from itertools import pairwise
from typing import Any

from backtesting.evaluation import evaluate_binary


def brier(probabilities: list[float], outcomes: list[int]) -> float:
    if not outcomes or len(probabilities) != len(outcomes):
        raise ValueError("non-empty equal-length inputs required")
    return sum((probability - outcome) ** 2
               for probability, outcome in zip(probabilities, outcomes)) / len(outcomes)


def calibration_table(probabilities: list[float], outcomes: list[int],
                      edges: list[float]) -> list[dict[str, float | int]]:
    if sorted(edges) != edges or len(edges) < 2:
        raise ValueError("calibration edges must be sorted")
    rows = []
    for index, (low, high) in enumerate(pairwise(edges)):
        members = [(p, y) for p, y in zip(probabilities, outcomes)
                   if low <= p < high or index == len(edges) - 2 and p == high]
        rows.append({
            "lower": low, "upper": high, "n": len(members),
            "predicted_mean": sum(p for p, _ in members) / len(members) if members else 0.0,
            "observed_rate": sum(y for _, y in members) / len(members) if members else 0.0,
            "positive_count": sum(y for _, y in members),
        })
    return rows


def tie_aware_top_group(probabilities: list[float], outcomes: list[int],
                        fraction: float = 0.2) -> dict[str, float | int]:
    if not 0 < fraction <= 1 or not outcomes:
        raise ValueError("invalid top-group inputs")
    ranked = sorted(zip(probabilities, outcomes), key=lambda pair: pair[0], reverse=True)
    boundary_index = max(1, math.ceil(len(ranked) * fraction)) - 1
    boundary = ranked[boundary_index][0]
    group = [(p, y) for p, y in ranked if p >= boundary]
    overall = sum(outcomes) / len(outcomes)
    rate = sum(y for _, y in group) / len(group)
    return {"requested_fraction": fraction, "boundary_probability": boundary,
            "n": len(group), "positive_count": sum(y for _, y in group),
            "event_rate": rate, "overall_event_rate": overall,
            "lift": rate / overall if overall else 0.0}


def percentile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("empty percentile")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def clustered_bootstrap(rows: list[dict[str, Any]], replicates: int = 2000,
                        seed: int = 20260813) -> dict[str, dict[str, float] | int]:
    by_company: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_company[row["stable_id"]].append(row)
    companies = sorted(by_company)
    if len(companies) < 2:
        raise ValueError("clustered bootstrap needs at least two companies")
    randomiser = random.Random(seed)
    samples: dict[str, list[float]] = defaultdict(list)
    for _ in range(replicates):
        selected = [randomiser.choice(companies) for _ in companies]
        sample = [dict(row) for company in selected for row in by_company[company]]
        probabilities = [float(row["probability"]) for row in sample]
        outcomes = [int(row["outcome"]) for row in sample]
        prior = [float(row["constant_prior"]) for row in sample]
        evaluation = evaluate_binary(probabilities, outcomes)
        samples["brier_difference_vs_prior"].append(brier(probabilities, outcomes) - brier(prior, outcomes))
        if evaluation.roc_auc is not None:
            samples["roc_auc"].append(evaluation.roc_auc)
        samples["average_precision"].append(evaluation.average_precision)
        samples["event_rate"].append(sum(outcomes) / len(outcomes))
        samples["top_group_lift"].append(tie_aware_top_group(probabilities, outcomes)["lift"])
    return {
        "replicates": replicates,
        **{name: {"lower_95": percentile(values, 0.025), "median": percentile(values, 0.5),
                  "upper_95": percentile(values, 0.975)} for name, values in samples.items() if values},
    }


def evaluate_rows(rows: list[dict[str, Any]], calibration_edges: list[float]) -> dict[str, Any]:
    probabilities = [float(row["probability"]) for row in rows]
    outcomes = [int(row["outcome"]) for row in rows]
    evaluation = evaluate_binary(probabilities, outcomes)
    result = evaluation.__dict__.copy()
    result["calibration"] = calibration_table(probabilities, outcomes, calibration_edges)
    result["top_risk_group"] = tie_aware_top_group(probabilities, outcomes)
    result["brier_skill_vs_constant_prior"] = 1 - brier(probabilities, outcomes) / brier(
        [float(row["constant_prior"]) for row in rows], outcomes)
    return result


def sensitivity(rows: list[dict[str, Any]], calibration_edges: list[float]) -> dict[str, Any]:
    def group(field: str) -> dict[str, Any]:
        values = defaultdict(list)
        for row in rows:
            values[row[field]].append(row)
        return {name: evaluate_rows(members, calibration_edges) for name, members in sorted(values.items())}

    leave_company = {}
    for company in sorted({row["stable_id"] for row in rows}):
        retained = [row for row in rows if row["stable_id"] != company]
        leave_company[company] = evaluate_rows(retained, calibration_edges)
    leave_sector = {}
    for sector in sorted({row["stratum"] for row in rows}):
        retained = [row for row in rows if row["stratum"] != sector]
        leave_sector[sector] = evaluate_rows(retained, calibration_edges)
    return {"by_cutoff": group("cutoff"), "by_sector": group("stratum"),
            "leave_one_company_out": leave_company, "leave_one_sector_out": leave_sector}


def lead_time_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [int(row["lead_time_days"]) for row in rows if int(row["outcome"]) == 1]
    return {"count": len(values), "values": values,
            "median": statistics.median(values) if values else None,
            "mean": statistics.mean(values) if values else None,
            "minimum": min(values) if values else None, "maximum": max(values) if values else None}

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "config/models/restructuring_rules_1_0_0.json"
BASELINES_PATH = ROOT / "config/baselines/restructuring_baselines_v2.json"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def specification_hash(path: str | Path) -> str:
    value = json.loads(Path(path).read_text())
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def predict_restructuring(features: dict[str, float], spec: dict[str, Any] | None = None) -> tuple[float, dict[str, float]]:
    spec = spec or load_json(MODEL_PATH)
    inputs = spec["inputs"]
    if set(features) != set(inputs):
        missing = sorted(set(inputs) - set(features))
        extra = sorted(set(features) - set(inputs))
        raise ValueError(f"feature mismatch; missing={missing}, extra={extra}")
    contributions: dict[str, float] = {}
    for name, definition in inputs.items():
        value = float(features[name])
        if not definition["minimum"] <= value <= definition["maximum"]:
            raise ValueError(f"{name} outside frozen range")
        contributions[name] = value * float(definition["weight"])
    prior = float(spec["transform"]["prior_probability"])
    logit = math.log(prior / (1 - prior)) + sum(contributions.values())
    probability = 1 / (1 + math.exp(-logit))
    decimals = int(spec["transform"]["probability_output_rounding_decimals"])
    return round(probability, decimals), contributions


def baseline_probabilities(features: dict[str, float], eligible_text: str,
                           company: str, development_outcomes: list[dict[str, Any]],
                           spec: dict[str, Any] | None = None) -> dict[str, float]:
    spec = spec or load_json(BASELINES_PATH)
    comparators = spec["comparators"]
    financial = comparators["financial_stress_rule"]
    for name in financial["inputs"]:
        if name not in features:
            raise ValueError(f"missing baseline feature: {name}")
    margin_flag = int(float(features["margin_pressure"]) >= 0.60)
    cash_flag = int(float(features["cash_pressure"]) >= 0.60)

    disclosure = comparators["disclosure_language_rule"]
    normalised = " ".join(unicodedata.normalize("NFKC", eligible_text).lower().split())
    excluded_spans = []
    for phrase in disclosure["excluded_context"]:
        excluded_spans.extend(match.span() for match in re.finditer(re.escape(phrase), normalised))
    triggered = False
    for term in disclosure["terms"]:
        for match in re.finditer(re.escape(term), normalised):
            if not any(abs(match.start() - start) <= 120 or abs(match.start() - end) <= 120
                       for start, end in excluded_spans):
                triggered = True
                break
        if triggered:
            break

    scored_development = [row for row in development_outcomes if row["status"] in {"positive", "negative"}]
    others = [int(row["occurred"]) for row in scored_development if row["company"] != company]
    if not others:
        raise ValueError("no development rows remain for leave-one-company-out baseline")

    logistic = comparators["financial_only_logistic"]
    standardised = {}
    for name in logistic["inputs"]:
        definition = logistic["standardisation"][name]
        standardised[name] = (float(features[name]) - definition["mean"]) / definition["population_std"]
    coefficients = logistic["coefficients"]
    financial_logit = (coefficients["intercept"]
                       + coefficients["margin_pressure_standardised"] * standardised["margin_pressure"]
                       + coefficients["cash_pressure_standardised"] * standardised["cash_pressure"])
    return {
        "constant_prior": float(comparators["constant_prior"]["probability"]),
        "leave_one_company_out_development_rate": sum(others) / len(others),
        "financial_stress_rule": (margin_flag + cash_flag + 1) / 5,
        "disclosure_language_rule": float(disclosure["probability_if_triggered"] if triggered
                                           else disclosure["probability_if_not_triggered"]),
        "financial_only_logistic": 1 / (1 + math.exp(-financial_logit)),
    }

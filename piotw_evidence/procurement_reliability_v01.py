from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Literal

FeatureRole = Literal[
    "INDEPENDENT CONDITION ELIGIBLE",
    "CORROBORATION ONLY",
    "FACTUAL ONLY",
    "RETIRED",
]


@dataclass(frozen=True)
class ReliabilityAwardRecord:
    source_record_id: str
    company_id: str
    legal_name: str
    company_number: str
    publication_year: int
    buyer: str
    category: str | None
    value: float | None
    currency: str | None
    underlying_award_id: str
    source_url: str
    source_hash: str
    exact_identifier: bool = True


def deduplicate_awards(records: list[ReliabilityAwardRecord]) -> tuple[list[ReliabilityAwardRecord], dict[str, list[str]]]:
    """Retain one record per company/underlying award and preserve version lineage."""
    retained: dict[tuple[str, str], ReliabilityAwardRecord] = {}
    lineage: dict[str, list[str]] = defaultdict(list)
    for row in sorted(records, key=lambda item: (item.company_id, item.publication_year, item.source_record_id)):
        key = (row.company_id, row.underlying_award_id)
        lineage[f"{row.company_id}:{row.underlying_award_id}"].append(row.source_record_id)
        retained.setdefault(key, row)
    return list(retained.values()), dict(lineage)


def procurement_coverage_diagnostics(
    records: list[ReliabilityAwardRecord], *, start_year: int, end_year: int
) -> dict[str, object]:
    retained, lineage = deduplicate_awards(records)
    periods = {year: [row for row in retained if row.publication_year == year]
               for year in range(start_year, end_year + 1)}
    buyers = Counter(row.buyer for row in retained)
    categories = Counter(row.category or "unknown" for row in retained)
    usable_values = [row for row in retained if row.value is not None and row.currency]
    usable_categories = [row for row in retained if row.category]
    total = len(retained)
    dominant_buyer = buyers.most_common(1)[0] if buyers else (None, 0)
    values_by_period: dict[int, float] = defaultdict(float)
    for row in usable_values:
        values_by_period[row.publication_year] += float(row.value or 0)
    period_value_shares = {}
    for year, rows in periods.items():
        values = [float(row.value or 0) for row in rows if row.value is not None]
        period_value_shares[str(year)] = max(values) / sum(values) if values and sum(values) else None
    return {
        "retained_unique_awards": total,
        "notice_versions_removed": len(records) - total,
        "deduplication_lineage": lineage,
        "award_count_by_period": {str(year): len(rows) if rows else None for year, rows in periods.items()},
        "periods_without_records": [year for year, rows in periods.items() if not rows],
        "buyer_count": len(buyers),
        "buyer_mix": dict(buyers),
        "dominant_buyer_share": dominant_buyer[1] / total if total else None,
        "category_mix": dict(categories),
        "usable_category_count": len(usable_categories),
        "usable_category_proportion": len(usable_categories) / total if total else 0.0,
        "usable_value_count": len(usable_values),
        "usable_value_proportion": len(usable_values) / total if total else 0.0,
        "disclosed_value_by_publication_period": {str(k): v for k, v in sorted(values_by_period.items())},
        "largest_award_value_share_by_period": period_value_shares,
        "exact_legal_entity_resolution_rate": (
            sum(row.exact_identifier for row in retained) / total if total else 0.0
        ),
        "source_regime_changes": [],
        "missingness_rule": "Periods without retained records are unavailable coverage, not zero activity.",
    }


def evaluate_negative_controls(diagnostics: dict[str, object]) -> dict[str, bool]:
    counts = [value for value in diagnostics["award_count_by_period"].values() if value is not None]
    value_shares = [value for value in diagnostics["largest_award_value_share_by_period"].values()
                    if value is not None]
    return {
        "one_buyer_repeated_publication": bool(
            diagnostics["dominant_buyer_share"] is not None
            and diagnostics["dominant_buyer_share"] >= 0.5
            and diagnostics["retained_unique_awards"] >= 2
        ),
        "multiple_notice_versions_one_award": diagnostics["notice_versions_removed"] > 0,
        "mostly_missing_values": diagnostics["usable_value_proportion"] < 0.5,
        "one_large_award_dominates_period": bool(value_shares and max(value_shares) >= 0.8),
        "volatile_counts_without_broader_change": bool(
            len(counts) >= 3 and max(counts) - min(counts) >= 2
            and (diagnostics["buyer_count"] <= 2 or diagnostics["usable_category_proportion"] < 0.75)
        ),
        "too_little_coverage": diagnostics["retained_unique_awards"] < 4,
    }


def enforce_feature_roles(
    features: dict[str, object], roles: dict[str, FeatureRole], *, external_candidate_present: bool = False
) -> dict[str, object]:
    independent = [name for name, role in roles.items()
                   if role == "INDEPENDENT CONDITION ELIGIBLE" and features.get(name) is not None]
    corroborating = [name for name, role in roles.items()
                     if role == "CORROBORATION ONLY" and features.get(name) is not None
                     and external_candidate_present]
    factual = [name for name, role in roles.items()
               if role == "FACTUAL ONLY" and features.get(name) is not None]
    retired = [name for name, role in roles.items() if role == "RETIRED"]
    return {
        "independent_condition_features": independent,
        "corroborating_features": corroborating,
        "factual_only_features": factual,
        "retired_features": retired,
        "may_emit_independent_condition": bool(independent),
    }

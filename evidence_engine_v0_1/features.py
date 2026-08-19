from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from datetime import UTC, date, datetime

from evidence_engine_v0_1.models import Event, FeatureSnapshot, Observation

NUMERIC_FEATURES = {
    "revenue": ("revenue_yoy_change_pct", "percent", "pct_change"),
    "operating_margin": ("operating_margin_change_bps", "basis_points", "bps_change"),
    "free_cash_flow": ("free_cash_flow_change_pct", "percent", "pct_change"),
    "net_debt": ("net_debt_change_pct", "percent", "pct_change"),
    "cash_conversion": ("cash_conversion_change_bps", "basis_points", "bps_change"),
    "capex": ("capex_growth_pct", "percent", "pct_change"),
    "restructuring_charges": ("restructuring_charge_change_pct", "percent", "pct_change"),
    "impairment_charges": ("impairment_change_pct", "percent", "pct_change"),
    "exceptional_costs": ("exceptional_cost_change_pct", "percent", "pct_change"),
}


def eligible_observations(observations: list[Observation], as_of_date: date) -> list[Observation]:
    return [o for o in observations if o.information_available_at.date() <= as_of_date and o.validation_status in {"accepted", "corrected"}]


def _snapshot(company: str, feature: str, as_of: date, value, unit: str, calculation: str,
              observations: list[Observation] | None = None,
              events: list[Event] | None = None) -> FeatureSnapshot:
    observations = observations or []
    events = events or []
    obs_ids = [o.observation_id for o in observations]
    event_ids = [e.event_id for e in events]
    evidence = sorted({o.source_evidence_id for o in observations})
    identity = hashlib.sha256(f"{company}|{feature}|0.1.0|{as_of}".encode()).hexdigest()[:16]
    quality_values = [o.extraction_confidence for o in observations] + [e.extraction_confidence for e in events]
    return FeatureSnapshot(feature_snapshot_id=f"fs-{identity}", company_id=company,
        feature_id=feature, feature_version="0.1.0", as_of_date=as_of, value=value, unit=unit,
        calculation=calculation, input_observation_ids=obs_ids, input_event_ids=event_ids,
        evidence_ids=evidence, quality=min(quality_values) if quality_values else 0,
        created_at=datetime.now(UTC))


def calculate_longitudinal_features(company_id: str, observations: list[Observation],
                                    events: list[Event], as_of_date: date) -> list[FeatureSnapshot]:
    eligible = [o for o in eligible_observations(observations, as_of_date) if o.company_id == company_id]
    output = []
    for metric, (feature, unit, method) in NUMERIC_FEATURES.items():
        values = sorted((o for o in eligible if o.observation_type == metric and isinstance(o.value, (int, float))),
                        key=lambda o: (o.observation_date or o.publication_date, o.reporting_period))
        if len(values) < 2:
            continue
        previous, current = values[-2:]
        if previous.currency != current.currency or previous.unit != current.unit:
            continue
        if method == "bps_change":
            value = (float(current.value) - float(previous.value)) * 100
        elif float(previous.value) == 0:
            continue
        else:
            value = (float(current.value) / float(previous.value) - 1) * 100
        output.append(_snapshot(company_id, feature, as_of_date, round(value, 6), unit,
            f"{current.value} compared with {previous.value}; {method}", [previous, current]))

    eligible_events = [e for e in events if e.company_id == company_id and e.information_available_at.date() <= as_of_date]
    by_type_period: dict[str, Counter] = defaultdict(Counter)
    event_by_type: dict[str, list[Event]] = defaultdict(list)
    for event in eligible_events:
        by_type_period[event.event_type][event.reporting_period] += 1
        event_by_type[event.event_type].append(event)
    for event_type, periods in by_type_period.items():
        ordered = sorted(periods)
        current_count = periods[ordered[-1]]
        prior_count = periods[ordered[-2]] if len(ordered) > 1 else 0
        selected = event_by_type[event_type]
        output.extend([
            _snapshot(company_id, f"{event_type}_count", as_of_date, current_count, "count",
                      f"count in {ordered[-1]}", events=selected),
            _snapshot(company_id, f"{event_type}_mentions_change", as_of_date,
                      current_count - prior_count, "count", f"{current_count} - {prior_count}", events=selected),
            _snapshot(company_id, f"{event_type}_new_flag", as_of_date,
                      int(len(ordered) == 1 or prior_count == 0), "boolean", "1 when absent in prior period", events=selected),
            _snapshot(company_id, f"{event_type}_persistence_periods", as_of_date,
                      len(ordered), "periods", "number of reporting periods containing event", events=selected),
        ])
    return sorted(output, key=lambda item: item.feature_id)

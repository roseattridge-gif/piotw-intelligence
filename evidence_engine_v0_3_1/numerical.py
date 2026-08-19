from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CanonicalNumericValue:
    metric_type: str
    reported_value: float
    normalized_value: float
    normalization: str
    accounting_basis: str


def canonicalize_numeric(metric_type: str, reported_value: float, accounting_basis: str | None) -> CanonicalNumericValue:
    """Preserve the source sign; capex features use positive economic magnitude."""
    normalized = abs(reported_value) if metric_type == "capex" else reported_value
    rule = "absolute economic expenditure magnitude; reported sign preserved separately" if metric_type == "capex" else "identity"
    accounting_basis = accounting_basis or "unclear"
    if accounting_basis not in {"statutory", "adjusted", "company_defined", "unclear"}:
        raise ValueError(f"unsupported accounting basis: {accounting_basis}")
    return CanonicalNumericValue(metric_type, reported_value, normalized, rule, accounting_basis)

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime

from evidence_engine_v0_1.models import Observation, RawEvidence

PARSER_VERSION = "report-regex-0.1.0"

METRICS = {
    "revenue": ["revenue"],
    "ebitda": ["ebitda", "adjusted ebitda"],
    "operating_profit": ["operating profit"],
    "operating_margin": ["operating margin"],
    "gross_margin": ["gross margin"],
    "operating_cash_flow": ["operating cash flow"],
    "free_cash_flow": ["free cash flow"],
    "cash_conversion": ["cash conversion"],
    "net_debt": ["net debt"],
    "net_cash": ["net cash"],
    "leverage": ["leverage"],
    "working_capital": ["working capital"],
    "inventory": ["inventory", "inventories"],
    "receivables": ["receivables"],
    "liquidity": ["liquidity"],
    "capex": ["capex", "capital expenditure"],
    "investment_commitments": ["investment commitments"],
    "restructuring_provisions": ["restructuring provisions"],
    "restructuring_charges": ["restructuring charges"],
    "exceptional_costs": ["exceptional costs"],
    "impairment_charges": ["impairment charges"],
    "redundancy_costs": ["redundancy costs"],
    "site_closure_costs": ["site closure costs"],
}

PERCENT_METRICS = {"operating_margin", "gross_margin", "cash_conversion"}
RATIO_METRICS = {"leverage"}


def parse_percentage(text: str) -> float:
    match = re.search(r"([-+]?\d+(?:\.\d+)?)\s*(?:%|percent\b|per cent\b)", text, re.IGNORECASE)
    if not match:
        raise ValueError(f"no percentage in {text!r}")
    return float(match.group(1))


def parse_numeric(text: str) -> tuple[float, str | None, str]:
    currency_match = re.search(r"(?:GBP|£|USD|\$|EUR|€)\s*([-+]?\d[\d,]*(?:\.\d+)?)\s*(bn|billion|m|million|k|thousand)?", text, re.IGNORECASE)
    if currency_match:
        value = float(currency_match.group(1).replace(",", ""))
        scale = (currency_match.group(2) or "").lower()
        multiplier = {"bn": 1000, "billion": 1000, "m": 1, "million": 1, "k": .001, "thousand": .001, "": 1}[scale]
        token = currency_match.group(0).upper()
        currency = "GBP" if "£" in token or "GBP" in token else "USD" if "$" in token or "USD" in token else "EUR"
        return value * multiplier, currency, "million"
    percent = re.search(r"([-+]?\d+(?:\.\d+)?)\s*(?:%|percent\b|per cent\b)", text, re.IGNORECASE)
    if percent:
        return float(percent.group(1)), None, "percent"
    ratio = re.search(r"([-+]?\d+(?:\.\d+)?)\s*x\b", text, re.IGNORECASE)
    if ratio:
        return float(ratio.group(1)), None, "times"
    raise ValueError(f"no supported numeric value in {text!r}")


def extract_financial_observations(evidence: RawEvidence) -> list[Observation]:
    observations = []
    current_page = None
    for line_number, raw_line in enumerate(evidence.raw_text.splitlines(), 1):
        line = raw_line.strip()
        page_match = re.fullmatch(r"\[PAGE (\d+)\]", line)
        if page_match:
            current_page = page_match.group(1)
            continue
        if ":" not in line:
            continue
        label, value_text = line.split(":", 1)
        normal = " ".join(label.lower().split())
        kind = next((metric for metric, aliases in METRICS.items() if normal in aliases), None)
        if not kind:
            continue
        try:
            value, currency, unit = parse_numeric(value_text)
        except ValueError:
            continue
        identity = hashlib.sha256(f"{evidence.evidence_id}|{line_number}|{kind}".encode()).hexdigest()[:16]
        observations.append(Observation(
            observation_id=f"obs-{identity}", company_id=evidence.company_id,
            observation_type=kind, reporting_period=evidence.reporting_period,
            value=value, unit=unit, currency=currency, source_evidence_id=evidence.evidence_id,
            evidence_span=line,
            page_or_section=f"page {current_page}, line {line_number}" if current_page else f"line {line_number}",
            publication_date=evidence.publication_date, observation_date=evidence.observation_date,
            information_available_at=evidence.information_available_at,
            extraction_confidence=0.99, parser_version=PARSER_VERSION,
            extraction_method="deterministic", extracted_at=datetime.now(UTC),
            quantified=True,
        ))
    return observations

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date

METRIC_TAGS = {
    "revenue": {"RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"},
    "operating_profit": {"OperatingIncomeLoss"},
    "operating_cash_flow": {"NetCashProvidedByUsedInOperatingActivities"},
    "capex": {"PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsForAdditionsToPropertyPlantAndEquipment"},
    "impairment_charges": {"AssetImpairmentCharges", "GoodwillAndIntangibleAssetImpairment"},
    "restructuring_charges": {"RestructuringCharges", "RestructuringAndRelatedCostIncurredCost"},
    "inventory": {"InventoryNet"},
    "receivables": {"AccountsReceivableNetCurrent"},
}
TAG_TO_METRIC = {tag: metric for metric, tags in METRIC_TAGS.items() for tag in tags}


@dataclass(frozen=True)
class Context:
    context_id: str
    start: str | None
    end: str
    has_dimensions: bool


@dataclass(frozen=True)
class NumericFact:
    metric: str
    taxonomy_tag: str
    value: float
    raw_value: str
    currency: str | None
    unit: str
    scale: int
    sign: int
    context_id: str
    period_start: str | None
    period_end: str
    period_role: str
    accounting_basis: str
    evidence_span: str


def attributes(tag: str) -> dict[str, str]:
    return {name.lower(): html.unescape(value) for name, _, value in
            re.findall(r"([\w:-]+)\s*=\s*(['\"])(.*?)\2", tag, re.DOTALL)}


def contexts(document: str) -> dict[str, Context]:
    output = {}
    for match in re.finditer(r"<xbrli:context\b([^>]*)>(.*?)</xbrli:context>", document,
                             re.IGNORECASE | re.DOTALL):
        attrs = attributes(match.group(1))
        body = match.group(2)
        start = re.search(r"<xbrli:startDate>([^<]+)", body, re.IGNORECASE)
        end = re.search(r"<xbrli:endDate>([^<]+)", body, re.IGNORECASE)
        instant = re.search(r"<xbrli:instant>([^<]+)", body, re.IGNORECASE)
        end_value = end.group(1) if end else instant.group(1) if instant else None
        if attrs.get("id") and end_value:
            output[attrs["id"]] = Context(attrs["id"], start.group(1) if start else None,
                end_value, bool(re.search(r"xbrldi:(?:explicitMember|typedMember)", body, re.IGNORECASE)))
    return output


def units(document: str) -> dict[str, tuple[str | None, str]]:
    output = {}
    for match in re.finditer(r"<xbrli:unit\b([^>]*)>(.*?)</xbrli:unit>", document,
                             re.IGNORECASE | re.DOTALL):
        attrs = attributes(match.group(1))
        measures = re.findall(r"<xbrli:measure>([^<]+)", match.group(2), re.IGNORECASE)
        value = " ".join(measures)
        currency = next((code for code in ("USD", "GBP", "EUR", "JPY", "CNY")
                         if f"iso4217:{code}" in value), None)
        unit = "currency" if currency else "shares" if "shares" in value.lower() else "pure"
        if attrs.get("id"):
            output[attrs["id"]] = (currency, unit)
    return output


def _number(text: str, attrs: dict[str, str]) -> tuple[float, int]:
    cleaned = html.unescape(re.sub(r"<[^>]+>", "", text)).strip()
    negative = attrs.get("sign") == "-" or cleaned.startswith("(") and cleaned.endswith(")")
    numeric = re.sub(r"[^0-9.\-]", "", cleaned.strip("()"))
    if not numeric or numeric in {"-", "."}:
        raise ValueError("not numeric")
    value = float(numeric)
    sign = -1 if negative and value > 0 else 1
    return value * sign, sign


def extract_numeric_facts(document: str, report_end: str) -> list[NumericFact]:
    context_map = contexts(document)
    unit_map = units(document)
    found = []
    pattern = re.compile(r"<ix:nonFraction\b([^>]*)>(.*?)</ix:nonFraction>",
                         re.IGNORECASE | re.DOTALL)
    for match in pattern.finditer(document):
        attrs = attributes(match.group(1))
        tag = attrs.get("name", "").split(":")[-1]
        metric = TAG_TO_METRIC.get(tag)
        context = context_map.get(attrs.get("contextref", ""))
        if not metric or not context or context.has_dimensions or context.end != report_end:
            continue
        try:
            raw, sign = _number(match.group(2), attrs)
        except ValueError:
            continue
        scale = int(attrs.get("scale", "0"))
        base_value = raw * 10 ** scale
        currency, raw_unit = unit_map.get(attrs.get("unitref", ""), (None, "unknown"))
        if currency:
            value, unit = base_value / 1_000_000, "million"
        else:
            value, unit = base_value, raw_unit
        start = context.start
        duration = (date.fromisoformat(context.end) - date.fromisoformat(start)).days if start else 0
        role = "current_fy" if duration >= 300 else "current_ytd" if duration >= 120 else "current_quarter" if start else "current_instant"
        span = match.group(0)
        found.append(NumericFact(metric, tag, value, html.unescape(re.sub(r"<[^>]+>", "", match.group(2))).strip(),
            currency, unit, scale, sign, context.context_id, start, context.end, role,
            "statutory" if attrs.get("name", "").lower().startswith("us-gaap:") else "company_adjusted_or_custom",
            span))
    unique = {}
    for fact in found:
        key = (fact.metric, fact.period_start, fact.period_end, fact.period_role,
               fact.accounting_basis, fact.currency, fact.value)
        unique.setdefault(key, fact)
    return sorted(unique.values(), key=lambda fact: (fact.metric, fact.period_role, fact.value))


def primary_facts(document: str, report_end: str) -> list[NumericFact]:
    """One consolidated current fact per metric; longest duration wins for flow metrics."""
    facts = extract_numeric_facts(document, report_end)
    chosen = {}
    for fact in facts:
        if fact.accounting_basis != "statutory":
            continue
        prior = chosen.get(fact.metric)
        if prior is None:
            chosen[fact.metric] = fact
            continue
        prior_days = ((date.fromisoformat(prior.period_end) - date.fromisoformat(prior.period_start)).days
                      if prior.period_start else 0)
        fact_days = ((date.fromisoformat(fact.period_end) - date.fromisoformat(fact.period_start)).days
                     if fact.period_start else 0)
        if fact_days > prior_days:
            chosen[fact.metric] = fact
    return sorted(chosen.values(), key=lambda fact: fact.metric)


def visible_text(document: str) -> str:
    text = re.sub(r"<(?:script|style|ix:hidden)\b.*?</(?:script|style|ix:hidden)>", " ", document,
                  flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(html.unescape(text).split())


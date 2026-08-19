from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser

METRIC_ALIASES = [
    ("adjusted_operating_margin", r"adjusted operating margin"),
    ("operating_margin", r"(?<!adjusted )operating margin"),
    ("adjusted_ebitda", r"adjusted (?:ebitda|earnings before interest,? taxes,? depreciation and amorti[sz]ation)"),
    ("ebitda", r"(?<!adjusted )(?:ebitda|earnings before interest,? taxes,? depreciation and amorti[sz]ation)"),
    ("adjusted_operating_profit", r"adjusted operating (?:profit|income)"),
    ("operating_profit", r"(?<!adjusted )operating (?:profit|income)"),
    ("free_cash_flow", r"free cash flow"),
    ("cash_conversion", r"cash conversion"),
    ("net_debt", r"net debt"),
    ("net_cash", r"net cash"),
    ("gross_margin", r"gross margin"),
    ("revenue", r"(?:revenue|net sales)"),
    ("capex", r"(?:capital expenditure|capital expenditures|capex)"),
    ("impairment", r"impairment (?:charge|charges|loss|losses)"),
    ("restructuring_charge", r"restructuring (?:charge|charges|cost|costs)"),
]


@dataclass(frozen=True)
class TableObservation:
    metric: str
    value: float
    unit: str
    scale: int
    currency: str | None
    period: str | None
    accounting_basis: str
    evidence_span: str


class _Tables(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr": self._row = []
        elif tag in {"td", "th"} and self._row is not None: self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None: self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).split())); self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row: self.rows.append(self._row)
            self._row = None


def parse_number(text: str) -> float | None:
    cleaned = text.strip().replace(",", "").replace("£", "").replace("$", "").replace("€", "")
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("() ").rstrip("%")
    if cleaned in {"", "-", "—", "n/a", "N/A"}: return None
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", cleaned): return None
    value = float(cleaned)
    return -abs(value) if negative else value


def extract_table_observations(html: str) -> list[TableObservation]:
    parser = _Tables(); parser.feed(html)
    context = " ".join(" ".join(row) for row in parser.rows[:8]).lower()
    currency = "GBP" if "£" in html else "USD" if "$" in html else "EUR" if "€" in html else None
    scale = 1_000_000_000 if "in billions" in context else 1_000_000 if "in millions" in context else 1_000 if "in thousands" in context else 1
    years: list[str] = []
    observations: list[TableObservation] = []
    seen: set[tuple] = set()
    for row in parser.rows:
        if not years:
            years = re.findall(r"\b(?:19|20)\d{2}\b", " ".join(row))
        label = row[0].lower() if row else ""
        match = next(((metric, pattern) for metric, pattern in METRIC_ALIASES if re.search(pattern, label)), None)
        if not match: continue
        metric = match[0]
        values = [parse_number(cell) for cell in row[1:]]
        values = [value for value in values if value is not None]
        for index, value in enumerate(values):
            unit = "percent" if "margin" in metric or metric == "cash_conversion" else "currency"
            applied_scale = 1 if unit == "percent" else scale
            basis = "adjusted" if metric.startswith("adjusted_") else "statutory_or_reported"
            key = (metric, value, index)
            if key in seen: continue
            seen.add(key)
            observations.append(TableObservation(metric, value * applied_scale, unit, applied_scale,
                currency if unit == "currency" else None, years[index] if index < len(years) else None,
                basis, " | ".join(row)))
    return observations

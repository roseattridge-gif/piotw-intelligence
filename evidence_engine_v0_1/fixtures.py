from __future__ import annotations

from datetime import UTC, datetime

from evidence_engine_v0_1.jobs import infer_function, infer_seniority
from evidence_engine_v0_1.models import JobRecord

COMPANIES = [f"synthetic-{index:02d}" for index in range(1, 11)]


def development_corpus() -> tuple[list[dict], dict]:
    """Twenty synthetic reports with a gold truth set; no locked-company material."""
    reports, numeric_gold, event_gold = [], {}, {}
    for index, company in enumerate(COMPANIES, 1):
        margin_2023 = 13.0 + index / 10
        margin_2024 = margin_2023 - (1.0 + index / 10)
        revenue_2023 = 100 + index * 10
        revenue_2024 = revenue_2023 * (0.97 + index / 100)
        debt_2023 = 40 + index * 5
        debt_2024 = debt_2023 * (1.1 + index / 100)
        for year, margin, revenue, debt, event_sentence, event_type in [
            (2023, margin_2023, revenue_2023, debt_2023,
             "The group reported strong order-book strength and revenue growth.", "order_book_strength"),
            (2024, margin_2024, revenue_2024, debt_2024,
             "Management launched a quantified cost-reduction programme covering 20 roles as demand weakened.", "cost_reduction"),
        ]:
            period = f"FY{year}"
            text = "\n".join([
                f"Revenue: GBP {revenue:.2f} million",
                f"Operating margin: {margin:.2f} percent",
                f"Free cash flow: GBP {30 + index - (year - 2023) * 4:.2f} million",
                f"Cash conversion: {90 - index - (year - 2023) * 5:.2f} percent",
                f"Net debt: GBP {debt:.2f} million",
                f"Capex: GBP {12 + index + (year - 2023) * 3:.2f} million",
                f"Restructuring charges: GBP {(year - 2023) * (2 + index / 10):.2f} million",
                event_sentence,
            ])
            row = {
                "company_id": company, "reporting_period": period,
                "source_type": "annual_report", "source_title": f"Synthetic {company} Annual Report {year}",
                "source_url": f"fixture://{company}/{year}", "period_end": f"{year}-12-31",
                "publication_date": f"{year + 1}-03-15",
                "information_available_at": f"{year + 1}-03-15T07:00:00+00:00",
                "collected_at": "2026-08-15T12:00:00+00:00", "text": text,
            }
            reports.append(row)
            numeric_gold[(company, period)] = {
                "revenue": round(revenue, 2), "operating_margin": round(margin, 2),
                "free_cash_flow": float(30 + index - (year - 2023) * 4),
                "cash_conversion": float(90 - index - (year - 2023) * 5),
                "net_debt": round(debt, 2), "capex": float(12 + index + (year - 2023) * 3),
                "restructuring_charges": round((year - 2023) * (2 + index / 10), 2),
            }
            event_gold[(company, period)] = {event_type, "growth_language" if year == 2023 else "demand_weakness"}
    return reports, {"numeric": numeric_gold, "events": event_gold}


def job_snapshots(company_id: str = "synthetic-01") -> tuple[list[JobRecord], list[JobRecord]]:
    previous_time = datetime(2024, 9, 30, 9, tzinfo=UTC)
    current_time = datetime(2024, 12, 31, 9, tzinfo=UTC)
    previous_titles = ["Plant Manager", "Production Engineer", "Operations Analyst", "Finance Manager", "Data Analyst", "Buyer"]
    current_titles = ["Transformation Director", "Data Lead", "AI Engineer", "Finance Manager"]

    def make(titles: list[str], observed: datetime) -> list[JobRecord]:
        return [JobRecord(company_id=company_id, posting_id=f"{title.lower().replace(' ', '-')}", title=title,
            function=infer_function(title), seniority=infer_seniority(title), location="London" if index % 2 else "Leeds",
            source_url=f"fixture://jobs/{title.lower().replace(' ', '-')}", collected_at=observed,
            first_seen=observed, last_seen=observed) for index, title in enumerate(titles)]
    return make(previous_titles, previous_time), make(current_titles, current_time)


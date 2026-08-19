from __future__ import annotations

import csv
import hashlib
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/evidence_engine_v0_2/corpus_manifest.csv"
RAW = ROOT / "data/evidence_engine_v0_2/raw"
SEC = "https://data.sec.gov"
ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
USER_AGENT = "PIOTW evidence research rose@roseattridge.com"
TICKERS = [
    "AAPL", "MSFT", "CAT", "DE", "HON", "GE", "F", "GM", "BA", "UPS",
    "FDX", "INTC", "AMD", "NVDA", "DELL", "HPQ", "MMM", "DOW", "EMN",
    "ALB", "NUE", "CLF", "CMI", "PH", "ETN",
]
FIELDS = ["document_id", "company", "ticker", "cik", "report_type", "form",
          "publication_date", "reporting_period", "source_url", "local_artifact",
          "sha256", "difficulty_flags", "difficulty_class", "development_partition_status"]


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                   "Accept-Encoding": "identity"})
    with urllib.request.urlopen(request, timeout=45) as response:
        body = response.read()
    time.sleep(0.12)
    return body


def difficulty_flags(html: str) -> list[str]:
    lower = html.lower()
    checks = {
        "dense_tables": len(re.findall(r"<table\b", lower)) >= 20,
        "adjusted_and_statutory": "adjusted" in lower and "statutory" in lower,
        "restated_prior_year": "restated" in lower,
        "multiple_currencies": sum(token in lower for token in ["usd", "gbp", "eur", "yen", "renminbi"]) >= 2,
        "acquisition_or_disposal": bool(re.search(r"acquisition|divestiture|disposal", lower)),
        "discontinued_operations": "discontinued operations" in lower,
        "segment_reorganisation": bool(re.search(r"segment.{0,80}(?:reorgan|realign|change)", lower)),
        "negative_bracketed_values": bool(re.search(r">\s*\(\s*\$?[\d,.]+\s*\)\s*<", lower)),
        "multiple_unit_scales": sum(token in lower for token in ["in millions", "in thousands", "in billions"]) >= 2,
        "duplicated_narrative_values": len(re.findall(r"revenue", lower)) >= 20,
        "embedded_multi_page_tables": len(re.findall(r"<table\b", lower)) >= 50,
    }
    return [name for name, matched in checks.items() if matched]


def choose_filings(recent: dict, ticker: str) -> list[int]:
    forms = recent["form"]
    dates = recent["filingDate"]
    items = recent.get("items", [""] * len(forms))
    eligible = [index for index, filed in enumerate(dates)
                if "2022-01-01" <= filed <= "2024-12-31"]
    annual = [i for i in eligible if forms[i] == "10-K"][:2]
    interim = [i for i in eligible if forms[i] == "10-Q"][:1]
    results = [i for i in eligible if forms[i] == "8-K" and "2.02" in items[i]][:1]
    preferred = interim if TICKERS.index(ticker) < 13 else results
    fallback = results if preferred is interim else interim
    return (annual + preferred + fallback)[:3]


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    ticker_rows = json.loads(fetch("https://www.sec.gov/files/company_tickers.json"))
    ticker_map = {row["ticker"].upper(): row for row in ticker_rows.values()}
    rows = []
    for ticker in TICKERS:
        profile = ticker_map[ticker]
        cik = f'{profile["cik_str"]:010d}'
        submissions = json.loads(fetch(f"{SEC}/submissions/CIK{cik}.json"))
        recent = submissions["filings"]["recent"]
        for index in choose_filings(recent, ticker):
            accession = recent["accessionNumber"][index]
            primary = recent["primaryDocument"][index]
            url = f"{ARCHIVES}/{int(cik)}/{accession.replace('-', '')}/{primary}"
            report_type = {"10-K": "annual_report", "10-Q": "interim_report",
                           "8-K": "regulatory_results_announcement"}[recent["form"][index]]
            document_id = f"ee02-{ticker.lower()}-{accession}"
            destination = RAW / ticker.lower() / f"{document_id}.html"
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                destination.write_bytes(fetch(url))
            body = destination.read_bytes()
            html = body.decode("utf-8", errors="replace")
            flags = difficulty_flags(html)
            rows.append({
                "document_id": document_id, "company": profile["title"], "ticker": ticker,
                "cik": cik, "report_type": report_type, "form": recent["form"][index],
                "publication_date": recent["filingDate"][index],
                "reporting_period": recent["reportDate"][index], "source_url": url,
                "local_artifact": str(destination.relative_to(ROOT)),
                "sha256": hashlib.sha256(body).hexdigest(),
                "difficulty_flags": "|".join(flags),
                "difficulty_class": "difficult" if len(flags) >= 3 else "ordinary",
                "development_partition_status": "external_us_development_no_outcomes",
            })
        print(f"{ticker}: {sum(row['ticker'] == ticker for row in rows)} filings")
    rows.sort(key=lambda row: (row["ticker"], row["publication_date"], row["document_id"]))
    with OUTPUT.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} real reports for {len({row['ticker'] for row in rows})} companies")


if __name__ == "__main__":
    main()

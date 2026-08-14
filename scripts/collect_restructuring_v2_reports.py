"""Collect conservative pre-cutoff annual-report sources without outcome access."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = [ROOT / "data/manifests/restructuring_validation.csv",
             ROOT / "data/manifests/restructuring_holdout.csv"]
RAW_ROOT = ROOT / "data/raw/restructuring_v2"
TEXT_ROOT = ROOT / "data/parsed/restructuring_v2"
INDEX = ROOT / "data/derived/restructuring_v2_source_index.json"
REPORT_YEAR = {"2020-12-31": 2019, "2022-12-31": 2021, "2024-12-31": 2023}
USER_AGENT = "PIOTW-Research/2.0 (+noncommercial validation; contact=operator)"
REQUEST_LOCK = threading.Lock()
LAST_REQUEST = 0.0


def candidate_urls(ticker: str, year: int) -> list[str]:
    clean = ticker.rstrip(".")
    first = clean[0].lower()
    base = f"https://www.annualreports.com/HostedData/AnnualReportArchive/{first}"
    return [f"{base}/LSE_{clean}_{year}.pdf", f"{base}/LSE_{clean}.L_{year}.pdf"]


def retrieve(url: str) -> bytes | None:
    global LAST_REQUEST
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/pdf"})
    for attempt in range(4):
        try:
            with REQUEST_LOCK:
                delay = 0.6 - (time.monotonic() - LAST_REQUEST)
                if delay > 0:
                    time.sleep(delay)
                with urlopen(request, timeout=45) as response:
                    body = response.read()
                LAST_REQUEST = time.monotonic()
            if not body.startswith(b"%PDF"):
                return None
            return body
        except HTTPError as exc:
            if exc.code == 404:
                return None
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 3:
                return None
            time.sleep(2 ** attempt)
        except (URLError, TimeoutError):
            if attempt == 3:
                return None
            time.sleep(2 ** attempt)
    return None


def extract_text(path: Path) -> tuple[str, int]:
    reader = PdfReader(path)
    return "\n\n".join(page.extract_text() or "" for page in reader.pages), len(reader.pages)


def collect_one(occasion_id: str, row: dict[str, str]) -> tuple[str, dict[str, object]]:
    year = REPORT_YEAR[row["cutoff"]]
    raw_path = RAW_ROOT / row["stable_id"] / f"annual-report-{year}.pdf"
    body = raw_path.read_bytes() if raw_path.exists() else None
    selected_url = ""
    if body is None:
        for url in candidate_urls(row["ticker"], year):
            body = retrieve(url)
            if body:
                selected_url = url
                break
    else:
        selected_url = candidate_urls(row["ticker"], year)[0]
    if not body:
        return occasion_id, {"status": "not_found", "ticker": row["ticker"],
                             "report_year": year, "attempted_urls": candidate_urls(row["ticker"], year)}
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(body)
    text_path = TEXT_ROOT / row["stable_id"] / f"annual-report-{year}.txt"
    text_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        text, page_count = extract_text(raw_path)
    except Exception as exc:  # noqa: BLE001 - source is preserved and failure recorded
        return occasion_id, {"status": "parse_failed", "ticker": row["ticker"],
                             "report_year": year, "url": selected_url,
                             "raw_path": str(raw_path.relative_to(ROOT)),
                             "raw_sha256": hashlib.sha256(body).hexdigest(), "reason": str(exc)}
    text_path.write_text(text)
    approval_dates = re.findall(
        r"(?:approved|signed)\s+(?:by\s+the\s+Board\s+)?on\s+(\d{1,2}\s+[A-Za-z]+\s+20\d{2})",
        text, flags=re.IGNORECASE)
    return occasion_id, {
        "status": "preserved", "ticker": row["ticker"], "report_year": year,
        "url": selected_url, "raw_path": str(raw_path.relative_to(ROOT)),
        "raw_sha256": hashlib.sha256(body).hexdigest(),
        "text_path": str(text_path.relative_to(ROOT)),
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "page_count": page_count, "approval_date_candidates": approval_dates[:10],
    }


def main() -> None:
    occasions = {}
    for manifest in MANIFESTS:
        for row in csv.DictReader(manifest.open()):
            occasions[row["occasion_id"]] = row
    existing = json.loads(INDEX.read_text()) if INDEX.exists() else {"sources": {}}
    sources = existing.get("sources", {})
    pending = [(occasion_id, row) for occasion_id, row in sorted(occasions.items())
               if sources.get(occasion_id, {}).get("status") != "preserved"]
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(collect_one, occasion_id, row): occasion_id
                   for occasion_id, row in pending}
        for number, future in enumerate(as_completed(futures), 1):
            occasion_id, result = future.result()
            sources[occasion_id] = result
            INDEX.parent.mkdir(parents=True, exist_ok=True)
            INDEX.write_text(json.dumps({"schema_version": "1", "sources": sources}, indent=2, sort_keys=True) + "\n")
            print(f"{number}/{len(pending)} {occasion_id}: {result['status']}", flush=True)
    INDEX.write_text(json.dumps({"schema_version": "1", "sources": sources}, indent=2, sort_keys=True) + "\n")
    preserved = sum(row.get("status") == "preserved" for row in sources.values())
    print(f"preserved {preserved}/{len(occasions)} sources")


if __name__ == "__main__":
    main()

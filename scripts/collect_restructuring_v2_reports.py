"""Collect conservative pre-cutoff annual-report sources without outcome access."""
from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
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
INDEX_LOCK = Path("/tmp/piotw-restructuring-v2-source-index.lock")
OFFICIAL_REGISTRY = ROOT / "data/restructuring_v2/official_source_registry.csv"
REPORT_YEAR = {"2020-12-31": 2019, "2022-12-31": 2021, "2024-12-31": 2023}
USER_AGENT = "Mozilla/5.0 (compatible; PIOTW-Research/2.0; noncommercial validation)"
REQUEST_LOCK = threading.Lock()
LAST_REQUEST = 0.0


def candidate_urls(ticker: str, year: int) -> list[str]:
    clean = ticker.rstrip(".")
    first = clean[0].lower()
    base = f"https://www.annualreports.com/HostedData/AnnualReportArchive/{first}"
    return [f"{base}/LSE_{clean}_{year}.pdf", f"{base}/LSE_{clean}.L_{year}.pdf"]


def retrieve(url: str, timeout: float, attempts: int) -> tuple[str, bytes | None, str]:
    global LAST_REQUEST
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/pdf"})
    for attempt in range(attempts):
        try:
            with REQUEST_LOCK:
                delay = 0.6 - (time.monotonic() - LAST_REQUEST)
                if delay > 0:
                    time.sleep(delay)
                with urlopen(request, timeout=timeout) as response:
                    body = response.read()
                LAST_REQUEST = time.monotonic()
            if not body.startswith(b"%PDF"):
                return "invalid_content", None, "response was not a PDF"
            return "preserved", body, ""
        except HTTPError as exc:
            if exc.code == 404:
                return "not_found", None, "HTTP 404"
            if exc.code not in {429, 500, 502, 503, 504} or attempt == attempts - 1:
                return "retrieval_failed", None, f"HTTP {exc.code}"
            time.sleep(2 ** attempt)
        except (URLError, TimeoutError) as exc:
            if attempt == attempts - 1:
                return "retrieval_failed", None, str(exc)
            time.sleep(2 ** attempt)
    return "retrieval_failed", None, "retry budget exhausted"


def extract_text(path: Path) -> tuple[str, int]:
    reader = PdfReader(path)
    return "\n\n".join(page.extract_text() or "" for page in reader.pages), len(reader.pages)


def read_sources() -> dict[str, dict[str, object]]:
    document = json.loads(INDEX.read_text()) if INDEX.exists() else {"sources": {}}
    return document.get("sources", {})


def record_source(occasion_id: str, result: dict[str, object]) -> None:
    """Merge one result under a cross-process lock; never overwrite unrelated fresh results."""
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    with INDEX_LOCK.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        sources = read_sources()
        current = sources.get(occasion_id, {})
        # A late timeout from an older worker must never downgrade preserved bytes.
        if current.get("status") != "preserved" or result.get("status") == "preserved":
            sources[occasion_id] = result
        INDEX.write_text(json.dumps(
            {"schema_version": "1", "sources": sources}, indent=2, sort_keys=True
        ) + "\n")


def collect_one(occasion_id: str, row: dict[str, str], timeout: float,
                attempts: int, official_url: str = "") -> tuple[str, dict[str, object]]:
    year = REPORT_YEAR[row["cutoff"]]
    raw_path = RAW_ROOT / row["stable_id"] / f"annual-report-{year}.pdf"
    body = raw_path.read_bytes() if raw_path.exists() else None
    selected_url = ""
    attempted = []
    failures = []
    if body is None:
        urls = ([official_url] if official_url else []) + candidate_urls(row["ticker"], year)
        for url in urls:
            status, body, reason = retrieve(url, timeout, attempts)
            attempted.append(url)
            if status == "preserved":
                selected_url = url
                break
            failures.append({"url": url, "status": status, "reason": reason})
    else:
        selected_url = official_url or candidate_urls(row["ticker"], year)[0]
    if not body:
        status = "not_found" if failures and all(
            item["status"] == "not_found" for item in failures) else "retrieval_failed"
        return occasion_id, {"status": status, "ticker": row["ticker"],
                             "report_year": year, "attempted_urls": attempted,
                             "attempt_results": failures}
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
        "retrieved_at": datetime.now(UTC).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0,
                        help="maximum unresolved occasions to probe; zero means all")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--retry-existing", action="store_true",
                        help="retry occasions already recorded as unavailable or failed")
    parser.add_argument("--occasion-id", action="append", default=[],
                        help="collect only the named occasion; repeat for multiple occasions")
    arguments = parser.parse_args()
    occasions = {}
    for manifest in MANIFESTS:
        for row in csv.DictReader(manifest.open()):
            occasions[row["occasion_id"]] = row
    official_urls = ({row["occasion_id"]: row["source_url"]
                      for row in csv.DictReader(OFFICIAL_REGISTRY.open())}
                     if OFFICIAL_REGISTRY.exists() else {})
    sources = read_sources()
    pending = [(occasion_id, row) for occasion_id, row in sorted(occasions.items())
               if occasion_id not in sources]
    if arguments.retry_existing:
        pending.extend((occasion_id, occasions[occasion_id]) for occasion_id in sorted(sources)
                       if occasion_id in occasions and sources[occasion_id].get("status") != "preserved")
    if arguments.occasion_id:
        requested = set(arguments.occasion_id)
        pending = [(occasion_id, row) for occasion_id, row in pending if occasion_id in requested]
    if arguments.limit:
        pending = pending[:arguments.limit]
    with ThreadPoolExecutor(max_workers=arguments.workers) as executor:
        futures = {executor.submit(collect_one, occasion_id, row, arguments.timeout,
                                   arguments.attempts, official_urls.get(occasion_id, "")): occasion_id
                   for occasion_id, row in pending}
        for number, future in enumerate(as_completed(futures), 1):
            occasion_id, result = future.result()
            record_source(occasion_id, result)
            print(f"{number}/{len(pending)} {occasion_id}: {result['status']}", flush=True)
    sources = read_sources()
    preserved = sum(row.get("status") == "preserved" for row in sources.values())
    print(f"preserved {preserved}/{len(occasions)} sources")


if __name__ == "__main__":
    main()

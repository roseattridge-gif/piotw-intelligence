from __future__ import annotations

import csv
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_2.ixbrl import visible_text
from evidence_engine_v0_3_4.events import extract_event_pipeline
from scripts.run_model_backed_v034 import CollectingVerifier

DATA = ROOT / "data/evidence_engine_v0_3_5"
SOURCES = DATA / "fresh_sources"

SELECTED = {
    "pep-0000077476-26-000007.html": ("PEPSICO INC", "PEP", "10-K", "2026-02-03", "2025-12-27", "https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm"),
    "pep-0000077476-26-000035.html": ("PEPSICO INC", "PEP", "10-Q", "2026-07-09", "2026-06-13", "https://www.sec.gov/Archives/edgar/data/77476/000007747626000035/pep-20260613.htm"),
    "rtx-0000101829-26-000006.html": ("RTX Corp", "RTX", "10-K", "2026-02-06", "2025-12-31", "https://www.sec.gov/Archives/edgar/data/101829/000010182926000006/rtx-20251231.htm"),
    "rtx-0000101829-26-000027.html": ("RTX Corp", "RTX", "10-Q", "2026-07-23", "2026-06-30", "https://www.sec.gov/Archives/edgar/data/101829/000010182926000027/rtx-20260630.htm"),
    "csco-0000858877-25-000111.html": ("CISCO SYSTEMS, INC.", "CSCO", "10-K", "2025-09-03", "2025-07-26", "https://www.sec.gov/Archives/edgar/data/858877/000085887725000111/csco-20250726.htm"),
    "csco-0000858877-26-000078.html": ("CISCO SYSTEMS, INC.", "CSCO", "10-Q", "2026-05-19", "2026-04-25", "https://www.sec.gov/Archives/edgar/data/858877/000085887726000078/csco-20260425.htm"),
    "lmt-0001628280-26-004195.html": ("LOCKHEED MARTIN CORP", "LMT", "10-K", "2026-01-29", "2025-12-31", "https://www.sec.gov/Archives/edgar/data/936468/000162828026004195/lmt-20251231.htm"),
    "lmt-0001628280-26-049411.html": ("LOCKHEED MARTIN CORP", "LMT", "10-Q", "2026-07-23", "2026-06-28", "https://www.sec.gov/Archives/edgar/data/936468/000162828026049411/lmt-20260628.htm"),
    "nke-0000320187-26-000088.html": ("NIKE, Inc.", "NKE", "10-K", "2026-07-15", "2026-05-31", "https://www.sec.gov/Archives/edgar/data/320187/000032018726000088/nke-20260531.htm"),
    "nke-0000320187-26-000037.html": ("NIKE, Inc.", "NKE", "10-Q", "2026-04-01", "2026-02-28", "https://www.sec.gov/Archives/edgar/data/320187/000032018726000037/nke-20260228.htm"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prior_material() -> tuple[set[str], set[str], set[str], set[str]]:
    companies: set[str] = set(); tickers: set[str] = set(); urls: set[str] = set(); hashes: set[str] = set()
    for path in ROOT.glob("data/evidence_engine_v0_*/**/*.csv"):
        if "v0_3_5" in str(path):
            continue
        try:
            for row in csv.DictReader(path.open(errors="ignore")):
                companies.add(row.get("company", "").casefold())
                tickers.add(row.get("ticker", "").casefold())
                urls.add(row.get("source_url", ""))
                if len(row.get("sha256", "")) == 64:
                    hashes.add(row["sha256"])
        except (csv.Error, UnicodeDecodeError):
            continue
    return companies, tickers, urls, hashes


def main() -> None:
    companies, tickers, urls, hashes = prior_material()
    manifest: list[dict[str, str]] = []
    candidates: list[dict[str, object]] = []
    for index, (name, meta) in enumerate(SELECTED.items(), 1):
        company, ticker, form, publication, period, url = meta
        path = SOURCES / name
        digest = sha(path)
        checks = {
            "company_unused": company.casefold() not in companies,
            "ticker_unused": ticker.casefold() not in tickers,
            "url_unused": url not in urls,
            "hash_unused": digest not in hashes,
        }
        if not all(checks.values()):
            raise RuntimeError(f"fresh-corpus contamination check failed for {name}: {checks}")
        document_id = f"ee035-fresh-{index:02d}-{ticker.lower()}"
        manifest.append({"document_id": document_id, "company": company, "ticker": ticker,
            "report_type": "annual_report" if form == "10-K" else "interim_report",
            "form": form, "publication_date": publication, "reporting_period": period,
            "source_url": url, "local_artifact": str(path.relative_to(ROOT)), "sha256": digest,
            "difficulty_flags": "tables|legal_accounting|historical_references|conditional_language|third_party_references|operational_changes|ordinary_reporting",
            "development_safe_status": "external_us_fresh_no_outcomes",
            **{key: str(value).lower() for key, value in checks.items()}})
        verifier = CollectingVerifier()
        extract_event_pipeline(visible_text(path.read_text(errors="ignore")), target_company=company,
            publication_date=publication, reporting_period=period, verifier=verifier)
        for number, candidate in enumerate(verifier.candidates, 1):
            raw = asdict(candidate)
            candidate_id = hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()[:24]
            candidates.append({"candidate_id": candidate_id, "document_id": document_id,
                "candidate_number": number, **raw})
    manifest_path = DATA / "fresh_corpus_manifest.csv"
    with manifest_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest[0])); writer.writeheader(); writer.writerows(manifest)
    candidates_path = DATA / "fresh_candidates.jsonl"
    candidates_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in candidates))
    freeze = {"freeze_version": "evidence-engine-v0.3.5-fresh-source-candidate-v1",
        "frozen_at": "2026-08-18", "companies": len({row['company'] for row in manifest}),
        "documents": len(manifest), "candidates": len(candidates), "outcomes_accessed": False,
        "semantic_v035_executed": False, "manifest_sha256": sha(manifest_path),
        "candidate_manifest_sha256": sha(candidates_path),
        "source_hashes": {row["document_id"]: row["sha256"] for row in manifest}}
    (DATA / "fresh_source_candidate_freeze.json").write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
    print(json.dumps(freeze, indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/evidence_engine_v0_3_7_independent"
SOURCES = DATA / "sources"
PACK = ROOT / "reviewer_pack_v0_3_7_independent"
FREEZE_DATE = "2026-08-19"
USER_AGENT = "PIOTW-Evidence-Engine/0.3.7 rose@roseattridge.com"

ISSUERS = (
    ("Adobe Inc.", "ADBE", "0001652044"),
    ("Intuit Inc.", "INTU", "0000896878"),
    ("ServiceNow, Inc.", "NOW", "0001373715"),
    ("Lam Research Corporation", "LRCX", "0000707549"),
    ("Applied Materials, Inc.", "AMAT", "0000006951"),
    ("General Mills, Inc.", "GIS", "0000040704"),
    ("Colgate-Palmolive Company", "CL", "0000021665"),
    ("Conagra Brands, Inc.", "CAG", "0000023217"),
    ("Waste Management, Inc.", "WM", "0000823768"),
    ("AutoZone, Inc.", "AZO", "0000866787"),
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read()


def prior_values() -> tuple[set[str], set[str], set[str], set[str]]:
    companies: set[str] = set()
    tickers: set[str] = set()
    urls: set[str] = set()
    hashes: set[str] = set()
    for path in ROOT.glob("data/**/*manifest*.csv"):
        if DATA in path.parents:
            continue
        try:
            for row in csv.DictReader(path.open(newline="")):
                companies.add(row.get("company", "").strip().casefold())
                tickers.add(row.get("ticker", "").strip().casefold())
                urls.add(row.get("source_url", "").strip())
                hashes.add(row.get("sha256", "").strip())
        except (OSError, csv.Error):
            continue
    return companies, tickers, urls, hashes


def filing(cik: str, form: str) -> dict[str, str]:
    submissions = json.loads(fetch(f"https://data.sec.gov/submissions/CIK{cik}.json"))
    recent = submissions["filings"]["recent"]
    for index, candidate in enumerate(recent["form"]):
        if candidate != form or recent["filingDate"][index] > FREEZE_DATE:
            continue
        accession = recent["accessionNumber"][index]
        primary = recent["primaryDocument"][index]
        accession_compact = accession.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_compact}/{primary}"
        return {
            "form": form,
            "filing_date": recent["filingDate"][index],
            "reporting_period": recent["reportDate"][index],
            "accession": accession,
            "primary_document": primary,
            "source_url": url,
        }
    raise RuntimeError(f"No eligible {form} found for CIK {cik}")


def main() -> None:
    protocol = ROOT / "docs/evidence-engine-v0.3.7-independent-validation-protocol.md"
    if not protocol.exists():
        raise RuntimeError("Preregistered protocol is missing")
    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    (PACK / "01 Official Source Documents").mkdir(parents=True, exist_ok=True)
    (PACK / "02 Blank Annotation Files").mkdir(parents=True, exist_ok=True)
    (PACK / "03 Reviewer Instructions").mkdir(parents=True, exist_ok=True)
    (PACK / "04 Corpus Manifest").mkdir(parents=True, exist_ok=True)

    prior_companies, prior_tickers, prior_urls, prior_hashes = prior_values()
    manifest: list[dict[str, str]] = []
    checks: list[dict[str, str | bool]] = []
    for company_index, (company, ticker, cik) in enumerate(ISSUERS, 1):
        company_unused = company.casefold() not in prior_companies
        ticker_unused = ticker.casefold() not in prior_tickers
        if not company_unused or not ticker_unused:
            raise RuntimeError(f"Contaminated issuer selection: {company} ({ticker})")
        for form_index, form in enumerate(("10-K", "10-Q"), 1):
            metadata = filing(cik, form)
            raw = fetch(metadata["source_url"])
            document_id = f"ee037-independent-{company_index:02d}-{form_index}-{ticker.lower()}"
            local = SOURCES / f"{document_id}.html"
            local.write_bytes(raw)
            sha = digest(local)
            url_unused = metadata["source_url"] not in prior_urls
            hash_unused = sha not in prior_hashes
            if not url_unused or not hash_unused:
                raise RuntimeError(f"Contaminated document selection: {document_id}")
            row = {
                "document_id": document_id,
                "company": company,
                "ticker": ticker,
                "cik": cik,
                "document_type": "annual_report" if form == "10-K" else "interim_report",
                **metadata,
                "local_artifact": str(local.relative_to(ROOT)),
                "sha256": sha,
                "development_safe_status": "UNSEEN_FROZEN_INDEPENDENT_VALIDATION",
            }
            manifest.append(row)
            checks.append({
                "document_id": document_id,
                "company_unused": company_unused,
                "ticker_unused": ticker_unused,
                "url_unused": url_unused,
                "hash_unused": hash_unused,
                "passed": all((company_unused, ticker_unused, url_unused, hash_unused)),
            })
            shutil.copy2(local, PACK / "01 Official Source Documents" / local.name)

    manifest_path = DATA / "corpus_manifest.csv"
    with manifest_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(manifest[0]))
        writer.writeheader()
        writer.writerows(manifest)
    contamination_path = DATA / "contamination_check.json"
    contamination_path.write_text(json.dumps({"status": "PASS", "checks": checks}, indent=2) + "\n")
    shutil.copy2(manifest_path, PACK / "04 Corpus Manifest" / manifest_path.name)
    shutil.copy2(DATA / "blank_atomic_observations.csv", PACK / "02 Blank Annotation Files")
    shutil.copy2(DATA / "blank_document_completion.csv", PACK / "02 Blank Annotation Files")
    shutil.copy2(ROOT / "docs/evidence-engine-v0.3.7-independent-validation-labels.md", PACK / "03 Reviewer Instructions" / "reviewer-instructions.md")

    freeze = {
        "study": "evidence_engine_v0_3_7_independent_atomic_observation_validation",
        "status": "CORPUS_FROZEN_AWAITING_INDEPENDENT_HUMAN_LABELS",
        "frozen_at": datetime.now(UTC).isoformat(),
        "protocol_sha256": digest(protocol),
        "corpus_manifest_sha256": digest(manifest_path),
        "contamination_check_sha256": digest(contamination_path),
        "companies": len(ISSUERS),
        "documents": len(manifest),
        "source_hashes": {row["document_id"]: row["sha256"] for row in manifest},
        "one_run_remaining": 1,
        "scientific_gate_run": False,
        "formal_independent_human_gold_available": False,
    }
    freeze_path = DATA / "corpus_freeze_manifest.json"
    freeze_path.write_text(json.dumps(freeze, indent=2) + "\n")
    shutil.copy2(freeze_path, PACK / "04 Corpus Manifest" / freeze_path.name)
    pack_files = sorted(path for path in PACK.rglob("*") if path.is_file())
    (PACK / "PACK_SHA256SUMS.txt").write_text("".join(f"{digest(path)}  {path.relative_to(PACK)}\n" for path in pack_files))
    print(json.dumps(freeze, indent=2))


if __name__ == "__main__":
    main()

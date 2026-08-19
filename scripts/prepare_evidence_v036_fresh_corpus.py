from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_2.ixbrl import visible_text
from evidence_engine_v0_3_4.events import extract_event_pipeline
from evidence_engine_v0_3_6.families import route_family
from scripts.check_evidence_v036_contamination import check_manifest
from scripts.run_model_backed_v034 import CollectingVerifier

DATA = ROOT / "data/evidence_engine_v0_3_6"
SOURCES = DATA / "fresh_sources"

SELECTED = [
    ("JOHNSON & JOHNSON", "JNJ", "000020040626000016", "10-K", "2026-02-11", "2025-12-28", "jnj-20251228.htm", "200406"),
    ("JOHNSON & JOHNSON", "JNJ", "000020040626000153", "10-Q", "2026-07-23", "2026-06-28", "jnj-20260628.htm", "200406"),
    ("Tesla, Inc.", "TSLA", "000162828026003952", "10-K", "2026-01-29", "2025-12-31", "tsla-20251231.htm", "1318605"),
    ("Tesla, Inc.", "TSLA", "000162828026049270", "10-Q", "2026-07-23", "2026-06-30", "tsla-20260630.htm", "1318605"),
    ("AMAZON COM INC", "AMZN", "000101872426000004", "10-K", "2026-02-06", "2025-12-31", "amzn-20251231.htm", "1018724"),
    ("AMAZON COM INC", "AMZN", "000101872426000026", "10-Q", "2026-07-31", "2026-06-30", "amzn-20260630.htm", "1018724"),
    ("PFIZER INC", "PFE", "000007800326000026", "10-K", "2026-02-26", "2025-12-31", "pfe-20251231.htm", "78003"),
    ("PFIZER INC", "PFE", "000007800326000095", "10-Q", "2026-08-04", "2026-06-28", "pfe-20260628.htm", "78003"),
    ("TYSON FOODS, INC.", "TSN", "000010049325000095", "10-K", "2025-11-10", "2025-09-27", "tsn-20250927.htm", "100493"),
    ("TYSON FOODS, INC.", "TSN", "000010049326000058", "10-Q", "2026-08-03", "2026-06-27", "tsn-20260627.htm", "100493"),
    ("TARGET CORP", "TGT", "000002741926000016", "10-K", "2026-03-11", "2026-01-31", "tgt-20260131.htm", "27419"),
    ("TARGET CORP", "TGT", "000002741926000022", "10-Q", "2026-05-29", "2026-05-02", "tgt-20260502.htm", "27419"),
    ("UNION PACIFIC CORP", "UNP", "000010088526000037", "10-K", "2026-02-06", "2025-12-31", "unp-20251231.htm", "100885"),
    ("UNION PACIFIC CORP", "UNP", "000010088526000250", "10-Q", "2026-07-23", "2026-06-30", "unp-20260630.htm", "100885"),
]

BROAD_LOCATORS = {
    "restructuring": r"\b(?:restructur|structural simplification|operating model redesign|organisational redesign)\w*\b",
    "cost_reduction": r"\b(?:cost reduc|cost sav|cost-out|cost out|productivity initiative)\w*\b",
    "efficiency_programme": r"\b(?:efficiency programme|efficiency program|productivity programme|productivity program)\b",
    "workforce_reduction": r"\b(?:workforce reduction|headcount reduction|role elimination|layoffs?)\b",
    "redundancy": r"\b(?:redundan|severance)\w*\b",
    "hiring": r"\b(?:hiring|recruiting|recruited|new hires?)\b",
    "labour_constraint": r"\b(?:labou?r shortage|workforce shortage|strike|work stoppage)\b",
    "skills_investment": r"\b(?:skills investment|employee training|workforce training|upskilling)\b",
    "site_closure": r"\b(?:site closure|plant closure|factory closure|facility closure|closed .*?(?:site|plant|factory|facility))\b",
    "capacity_expansion": r"\b(?:capacity expansion|expanded capacity|increase capacity|new production line)\b",
    "capacity_reduction": r"\b(?:capacity reduction|reduced capacity|remove capacity)\b",
    "new_facility": r"\b(?:new facility|new plant|new factory|new warehouse|distribution cent(?:re|er))\b",
    "operational_disruption": r"\b(?:operational disruption|production disruption|production halt|temporarily shut|shutdown)\b",
    "growth_language": r"\b(?:revenue|sales|orders?|backlog|volume)\b.{0,80}\b(?:grew|growth|increased|declined|decreased|fell)\b",
    "demand_growth": r"\b(?:demand (?:grew|growth|increased)|increased demand|strong demand)\b",
    "demand_weakness": r"\b(?:demand weakness|weak demand|softening demand|demand declined|lower demand)\b",
    "order_book_strength": r"\b(?:order book|order-book|backlog)\b.{0,60}\b(?:strong|grew|increased|record)\b",
    "supply_chain_constraint": r"\b(?:supply chain|component shortage|material shortage|supplier disruption)\b",
    "supplier_diversification": r"\b(?:supplier diversification|additional suppliers?|second source|dual source)\b",
    "procurement_intervention": r"\b(?:procurement programme|procurement program|centralised procurement|centralized procurement)\b",
    "inventory_buffer": r"\b(?:safety stock|buffer stock|inventory buffer)\b",
    "supplier_insolvency": r"\b(?:supplier|vendor)\b.{0,50}\b(?:insolven|bankrupt|administration)\w*\b",
    "logistics_disruption": r"\b(?:logistics disruption|shipping disruption|shipment delays?)\b",
    "quality_failure": r"\b(?:quality issue|quality failure|quality problem|defect|nonconformance)\w*\b",
    "recall": r"\b(?:product recall|recall of|recalled)\b",
    "safety_issue": r"\b(?:safety incident|safety issue|workplace injury|fatality)\b",
    "compliance_breach": r"\b(?:compliance breach|non-compliance|noncompliance|violated .*?(?:law|regulation|permit))\b",
    "warranty_issue": r"\b(?:warranty claims?|warranty costs?|warranty issue)\b",
    "remediation_programme": r"\b(?:remediation programme|remediation program|corrective action programme|corrective action program)\b",
    "regulatory_investigation": r"\b(?:regulatory investigation|government investigation|investigation by .*?(?:agency|authority|regulator))\b",
    "regulatory_intervention": r"\b(?:regulatory action|enforcement action|consent decree|operating restriction)\b",
    "transformation": r"\b(?:business transformation|transformation programme|transformation program|transformation initiative)\b",
    "leadership_change": r"\b(?:appointed|named|resigned|stepped down|departed|succession)\b.{0,80}\b(?:chief executive|chief financial|chief operating|CEO|CFO|COO|president|chair)\b|\b(?:CEO|CFO|COO|chief executive|chief financial|chief operating)\b.{0,80}\b(?:appointed|resigned|departed|succession)\b",
}


def broad_candidates(text: str, company: str, publication: str, period: str) -> list[dict[str, object]]:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if 40 <= len(part.strip()) <= 1400]
    found: list[dict[str, object]] = []
    for index, sentence in enumerate(sentences):
        context = " ".join(sentences[max(0, index - 1): min(len(sentences), index + 2)])
        for event_type, pattern in BROAD_LOCATORS.items():
            if re.search(pattern, sentence, re.IGNORECASE):
                found.append({
                    "target_company": company,
                    "candidate_event_type": event_type,
                    "exact_candidate_span": sentence,
                    "context": context,
                    "heading": None,
                    "publication_date": publication,
                    "deterministic_metadata": {
                        "subject_type": "target_company",
                        "entity_scope": "unknown",
                        "factual_status": "unresolved",
                        "event_status": "unresolved",
                        "allowed_remaps": [],
                        "reporting_period": period,
                        "candidate_locator": "fresh_broad_source_locator_v1",
                    },
                })
    return found


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest: list[dict[str, str]] = []
    candidates: list[dict[str, object]] = []
    for index, (company, ticker, accession, form, publication, period, primary, cik) in enumerate(SELECTED, 1):
        source = SOURCES / f"{ticker.lower()}-{accession}.html"
        if not source.exists() or source.stat().st_size < 10_000:
            raise RuntimeError(f"missing or implausibly small fresh source: {source}")
        document_id = f"ee036-fresh-{index:02d}-{ticker.lower()}"
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary}"
        manifest.append({
            "document_id": document_id,
            "company": company,
            "ticker": ticker,
            "report_type": "annual_report" if form == "10-K" else "interim_report",
            "form": form,
            "publication_date": publication,
            "reporting_period": period,
            "source_url": url,
            "local_artifact": str(source.relative_to(ROOT)),
            "sha256": sha(source),
            "difficulty_flags": "tables|legal_accounting|historical|conditional|third_party|cross_family|operational",
            "development_safe_status": "fresh_validation_no_outcomes",
        })
        source_text = visible_text(source.read_text(errors="ignore"))
        verifier = CollectingVerifier()
        extract_event_pipeline(
            source_text,
            target_company=company,
            publication_date=publication,
            reporting_period=period,
            verifier=verifier,
        )
        for number, candidate in enumerate(verifier.candidates, 1):
            raw = asdict(candidate)
            candidate_id = hashlib.sha256(
                f"{document_id}|{number}|{json.dumps(raw, sort_keys=True)}".encode()
            ).hexdigest()[:24]
            candidates.append({
                "candidate_id": candidate_id,
                "document_id": document_id,
                "candidate_number": number,
                **raw,
            })
        for number, raw in enumerate(broad_candidates(source_text, company, publication, period), 1):
            candidate_id = hashlib.sha256(
                f"{document_id}|broad|{number}|{json.dumps(raw, sort_keys=True)}".encode()
            ).hexdigest()[:24]
            candidates.append({
                "candidate_id": candidate_id,
                "document_id": document_id,
                "candidate_number": f"broad-{number}",
                **raw,
            })

    unique: dict[tuple[str, str, str], dict[str, object]] = {}
    for row in candidates:
        key = (str(row["document_id"]), str(row["candidate_event_type"]), str(row["exact_candidate_span"]))
        unique.setdefault(key, row)
    by_family: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in unique.values():
        family = route_family(str(row["candidate_event_type"]))
        if family:
            by_family[family].append(row)
    candidates = []
    for family in sorted(by_family):
        ranked = sorted(
            by_family[family],
            key=lambda row: hashlib.sha256(
                f"{row['document_id']}|{row['candidate_event_type']}|{row['exact_candidate_span']}".encode()
            ).hexdigest(),
        )
        candidates.extend(ranked[:90])

    manifest_path = DATA / "fresh_candidate_manifest.csv"
    with manifest_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest[0]))
        writer.writeheader()
        writer.writerows(manifest)
    contamination = check_manifest(manifest_path)
    if contamination["status"] != "PASS":
        raise RuntimeError(f"fresh corpus contamination: {contamination}")
    candidate_path = DATA / "fresh_candidate_pool.jsonl"
    candidate_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in candidates))
    freeze = {
        "freeze_version": "evidence-engine-v0.3.6-fresh-source-pool-v1",
        "companies": len({row["company"] for row in manifest}),
        "documents": len(manifest),
        "candidate_pool": len(candidates),
        "manifest_sha256": sha(manifest_path),
        "candidate_pool_sha256": sha(candidate_path),
        "source_hashes": {row["document_id"]: row["sha256"] for row in manifest},
        "contamination": contamination,
        "semantic_v036_executed": False,
        "outcomes_accessed": False,
    }
    (DATA / "fresh_source_pool_freeze.json").write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
    print(json.dumps(freeze, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

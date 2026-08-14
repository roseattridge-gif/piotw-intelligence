"""Build audited v2 evidence/features from manually reviewed pre-cutoff packets."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path

from pypdf import PdfReader
from pypdf import __version__ as pypdf_version

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from validation.restructuring_v2_data import extraction_hash, write_csv

INDEX = ROOT / "data/derived/restructuring_v2_source_index.json"
QUEUE = ROOT / "data/derived/restructuring_v2_feature_review_queue.csv"
EVIDENCE = ROOT / "data/restructuring_v2/evidence.csv"
FEATURES = ROOT / "data/restructuring_v2/features.csv"
ISSUES = ROOT / "data/derived/restructuring_v2_evidence_issues.json"
OVERRIDES = ROOT / "data/restructuring_v2/source_availability_overrides.csv"
SCORE_FIELDS = ("pressure_language", "margin_pressure", "cash_pressure", "contrary_strength")
EVIDENCE_FIELDS = [
    "evidence_id", "occasion_id", "company", "ticker", "available_at", "availability_basis",
    "availability_evidence", "source_title", "source_url", "retrieved_at", "raw_path",
    "raw_sha256", "preservation_status", "parser_version", "source_location", "observation",
    "direction", "already_announced_exclusion", "extraction_sha256", "review_status",
]
FEATURE_FIELDS = ["occasion_id", *SCORE_FIELDS, "evidence_ids", "feature_review_status"]


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def reviewed_scores() -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for path in sorted((ROOT / "data/restructuring_v2").glob("feature_reviews_batch_*.csv")):
        for row in load_rows(path):
            if row["occasion_id"] in rows:
                raise ValueError(f"duplicate feature review: {row['occasion_id']}")
            for field in SCORE_FIELDS:
                value = float(row[field])
                if not 0 <= value <= 1 or round(value * 20) != value * 20:
                    raise ValueError(f"invalid 0.05-grid score at {row['occasion_id']}:{field}")
            if not row["reviewer"] or not row["review_note"]:
                raise ValueError(f"review attribution missing: {row['occasion_id']}")
            rows[row["occasion_id"]] = row
    return rows


def pdf_creation_date(path: Path) -> date | None:
    raw = PdfReader(path).metadata.get("/CreationDate") or ""
    match = re.match(r"D:(\d{4})(\d{2})(\d{2})", str(raw))
    return date(*map(int, match.groups())) if match else None


def plausible_approval_dates(source: dict[str, object]) -> list[date]:
    year = int(source["report_year"])
    result = []
    for raw in source.get("approval_date_candidates", []):
        compact = " ".join(str(raw).replace("\xa0", " ").split())
        try:
            parsed = datetime.strptime(compact, "%d %B %Y").replace(tzinfo=UTC).date()
        except ValueError:
            continue
        if year - 1 <= parsed.year <= year + 1:
            result.append(parsed)
    return result


def availability(source: dict[str, object], cutoff: date,
                 override: dict[str, str] | None) -> tuple[date, str, str] | None:
    if override:
        selected = date.fromisoformat(override["available_at"])
        if selected > cutoff:
            raise ValueError(f"availability override is after cutoff: {override['occasion_id']}")
        return selected, override["basis"], f"{override['evidence_url']} — {override['note']}"
    raw_path = ROOT / str(source["raw_path"])
    approvals = plausible_approval_dates(source)
    if approvals:
        selected = max(approvals)
        if selected <= cutoff:
            return selected, "document_approval_plus_archive_classification", selected.isoformat()
    created = pdf_creation_date(raw_path)
    if created and created <= cutoff:
        return created, "pdf_creation_plus_archive_classification", created.isoformat()
    return None


def page_locations(row: dict[str, str]) -> str:
    pages = sorted({int(item) for field in (
        "pressure_excerpts", "margin_excerpts", "cash_excerpts", "contrary_excerpts")
                    for item in re.findall(r"\[p\.(\d+)\]", row[field])})
    return "|".join(f"p.{page}" for page in pages)


def main() -> None:
    sources = json.loads(INDEX.read_text())["sources"]
    queue = {row["occasion_id"]: row for row in load_rows(QUEUE)}
    reviews = reviewed_scores()
    overrides = ({row["occasion_id"]: row for row in load_rows(OVERRIDES)}
                 if OVERRIDES.exists() else {})
    evidence_rows = []
    feature_rows = []
    issues = []
    for occasion_id, review in sorted(reviews.items()):
        if occasion_id not in queue or sources.get(occasion_id, {}).get("status") != "preserved":
            issues.append({"occasion_id": occasion_id, "reason": "preserved source or packet missing"})
            continue
        packet = queue[occasion_id]
        source = dict(sources[occasion_id])
        override = overrides.get(occasion_id)
        if override:
            source.update({name: override[name] for name in ("source_url", "raw_path", "raw_sha256")
                           if override.get(name)})
        cutoff = date.fromisoformat(packet["cutoff"])
        available = availability(source, cutoff, override)
        if available is None:
            issues.append({"occasion_id": occasion_id,
                           "reason": "pre-cutoff public availability not evidenced conservatively"})
            continue
        available_at, basis, basis_evidence = available
        raw_path = ROOT / source["raw_path"]
        evidence_id = f"ev-{occasion_id}-annual-report"
        excerpts = " || ".join(packet[field] for field in (
            "pressure_excerpts", "margin_excerpts", "cash_excerpts", "contrary_excerpts")
                                if packet[field])
        exclusion = review["review_note"] if "already" in review["review_note"].lower() else ""
        retrieved_at = source.get("retrieved_at") or datetime.fromtimestamp(
            raw_path.stat().st_mtime, tz=UTC).isoformat()
        evidence = {
            "evidence_id": evidence_id, "occasion_id": occasion_id,
            "company": packet["company"], "ticker": packet["ticker"],
            "available_at": available_at.isoformat(), "availability_basis": basis,
            "availability_evidence": basis_evidence,
            "source_title": f"{packet['company']} Annual Report {packet['report_year']}",
            "source_url": source.get("source_url", source["url"]), "retrieved_at": retrieved_at,
            "raw_path": source["raw_path"], "raw_sha256": source["raw_sha256"],
            "preservation_status": "preserved", "parser_version": f"pypdf-{pypdf_version}+manual-1",
            "source_location": page_locations(packet),
            "observation": f"{review['review_note']} Supporting extracts: {excerpts}",
            "direction": "mixed", "already_announced_exclusion": exclusion,
            "extraction_sha256": "", "review_status": f"manual_primary_source:{review['reviewer']}",
        }
        evidence["extraction_sha256"] = extraction_hash(evidence)
        evidence_rows.append(evidence)
        feature_rows.append({"occasion_id": occasion_id,
                             **{field: review[field] for field in SCORE_FIELDS},
                             "evidence_ids": evidence_id,
                             "feature_review_status": f"manual:{review['reviewer']}"})
    write_csv(EVIDENCE, EVIDENCE_FIELDS, evidence_rows)
    write_csv(FEATURES, FEATURE_FIELDS, feature_rows)
    ISSUES.write_text(json.dumps({"issues": issues}, indent=2, sort_keys=True) + "\n")
    digest = hashlib.sha256(EVIDENCE.read_bytes() + FEATURES.read_bytes()).hexdigest()
    print(f"built {len(feature_rows)} reviewed feature rows; {len(issues)} issues; sha256 {digest[:12]}")


if __name__ == "__main__":
    main()

"""Prepare pre-cutoff-only excerpts for manual frozen-rubric scoring."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "data/derived/restructuring_v2_source_index.json"
OUTPUT = ROOT / "data/derived/restructuring_v2_feature_review_queue.csv"
FIELDS = ["occasion_id", "company", "ticker", "cutoff", "source_url", "report_year",
          "pressure_excerpts", "margin_excerpts", "cash_excerpts", "contrary_excerpts",
          "pressure_language", "margin_pressure", "cash_pressure", "contrary_strength",
          "reviewer", "review_note"]
TERMS = {
    "pressure_excerpts": ["restructur", "redundan", "closure", "consolidat", "efficien", "cost reduction",
                          "simplif", "right-size", "footprint", "operating model", "supply chain", "shortage"],
    "margin_excerpts": ["operating margin", "profit margin", "gross margin", "underlying margin"],
    "cash_excerpts": ["free cash flow", "cash conversion", "working capital", "net debt", "liquidity", "covenant"],
    "contrary_excerpts": ["order book", "record order", "strong demand", "revenue growth", "margin improved",
                          "cash generation", "liquidity", "recovery"],
}


def excerpts(pages: list[str], terms: list[str], limit: int = 8) -> str:
    matches = []
    occupied: dict[int, list[tuple[int, int]]] = {}
    for page_number, page in enumerate(pages, 1):
        compact = " ".join(page.split())
        for term in terms:
            for match in re.finditer(re.escape(term), compact, flags=re.IGNORECASE):
                start, end = max(0, match.start() - 180), min(len(compact), match.end() + 260)
                if any(not (end < old_start or start > old_end)
                       for old_start, old_end in occupied.setdefault(page_number, [])):
                    continue
                occupied[page_number].append((start, end))
                matches.append(f"[p.{page_number}] {compact[start:end]}")
                if len(matches) >= limit:
                    return " || ".join(matches)
    return " || ".join(matches)


def main() -> None:
    source_index = json.loads(INDEX.read_text())["sources"]
    manifests = {}
    for name in ("validation", "holdout"):
        for row in csv.DictReader((ROOT / f"data/manifests/restructuring_{name}.csv").open()):
            manifests[row["occasion_id"]] = row
    existing = ({row["occasion_id"]: row for row in csv.DictReader(OUTPUT.open())}
                if OUTPUT.exists() else {})
    rows = []
    for occasion_id, source in sorted(source_index.items()):
        if source.get("status") != "preserved" or occasion_id not in manifests:
            continue
        manifest = manifests[occasion_id]
        reader = PdfReader(ROOT / source["raw_path"])
        pages = [page.extract_text() or "" for page in reader.pages]
        prior = existing.get(occasion_id, {})
        rows.append({
            "occasion_id": occasion_id, "company": manifest["company"], "ticker": manifest["ticker"],
            "cutoff": manifest["cutoff"], "source_url": source["url"], "report_year": source["report_year"],
            **{name: excerpts(pages, terms) for name, terms in TERMS.items()},
            **{name: prior.get(name, "") for name in (
                "pressure_language", "margin_pressure", "cash_pressure",
                "contrary_strength", "reviewer", "review_note")},
        })
    with OUTPUT.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"prepared {len(rows)} pre-cutoff feature-review packets")


if __name__ == "__main__":
    main()

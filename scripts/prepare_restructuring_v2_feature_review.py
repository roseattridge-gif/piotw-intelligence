"""Prepare pre-cutoff-only excerpts for manual frozen-rubric scoring."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "data/derived/restructuring_v2_source_index.json"
OUTPUT = ROOT / "data/derived/restructuring_v2_feature_review_queue.csv"
OFFICIAL_REGISTRY = ROOT / "data/restructuring_v2/official_source_registry.csv"
REPORT_YEAR = {"2020-12-31": 2019, "2022-12-31": 2021, "2024-12-31": 2023}
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--occasion-id", action="append", default=[],
                        help="prepare only these occasions while retaining the existing queue")
    args = parser.parse_args()
    selected = set(args.occasion_id)
    source_index = json.loads(INDEX.read_text())["sources"]
    manifests = {}
    for name in ("validation", "holdout"):
        for row in csv.DictReader((ROOT / f"data/manifests/restructuring_{name}.csv").open()):
            manifests[row["occasion_id"]] = row
    existing = ({row["occasion_id"]: row for row in csv.DictReader(OUTPUT.open())}
                if OUTPUT.exists() else {})
    official_urls = ({row["occasion_id"]: row["source_url"]
                      for row in csv.DictReader(OFFICIAL_REGISTRY.open())}
                     if OFFICIAL_REGISTRY.exists() else {})
    rows = ([row for occasion_id, row in existing.items() if occasion_id not in selected]
            if selected else [])
    for occasion_id, source in sorted(source_index.items()):
        if source.get("status") != "preserved" or occasion_id not in manifests:
            continue
        if selected and occasion_id not in selected:
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
    # A full official PDF may be inspectable through a public web archive while direct
    # byte preservation is technically blocked. Keep a manifest packet so the audited
    # web-review path can record page-level evidence and the preservation limitation.
    for occasion_id in sorted(selected):
        if any(row["occasion_id"] == occasion_id for row in rows):
            continue
        manifest = manifests.get(occasion_id)
        if not manifest or occasion_id not in official_urls:
            continue
        prior = existing.get(occasion_id, {})
        rows.append({
            "occasion_id": occasion_id, "company": manifest["company"],
            "ticker": manifest["ticker"], "cutoff": manifest["cutoff"],
            "source_url": official_urls[occasion_id],
            "report_year": REPORT_YEAR[manifest["cutoff"]],
            **{name: "" for name in TERMS},
            **{name: prior.get(name, "") for name in (
                "pressure_language", "margin_pressure", "cash_pressure",
                "contrary_strength", "reviewer", "review_note")},
        })
    rows.sort(key=lambda row: row["occasion_id"])
    with OUTPUT.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"prepared {len(rows)} pre-cutoff feature-review packets")


if __name__ == "__main__":
    main()

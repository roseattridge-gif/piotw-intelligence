"""Deterministically select the v2 cohort and build outcome-blind partitions."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "research/restructuring_v2_candidate_universe.csv"
MANIFEST_DIR = ROOT / "data/manifests"
SEED = "piotw-restructuring-validation-v2-cohort-20260813"
QUOTA = 25
V1_TICKERS = {"SNR", "CHRT", "MRO", "ELM", "CRPR", "VCT", "RCDO", "IMI", "SPX", "PRV"}

FIELDS = ["occasion_id", "company", "ticker", "stable_id", "sector", "stratum", "cutoff",
          "window_end", "dataset_partition", "target", "horizon_days", "inclusion_status",
          "exclusion_reason", "selection_rank", "selection_hash"]


def selection_hash(stable_id: str) -> str:
    return hashlib.sha256(f"{SEED}|{stable_id}".encode()).hexdigest()


def write_manifest(name: str, rows: list[dict[str, str]]) -> None:
    path = MANIFEST_DIR / name
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def occasion(row: dict[str, str], cutoff: str, window_end: str, partition: str,
             rank: int, digest: str) -> dict[str, str]:
    return {
        "occasion_id": f"rv2-{row['ticker']}-{cutoff}", "company": row["company"],
        "ticker": row["ticker"], "stable_id": row["stable_id"], "sector": row["sector"],
        "stratum": row["stratum"], "cutoff": cutoff, "window_end": window_end,
        "dataset_partition": partition, "target": "restructuring_announced",
        "horizon_days": "365", "inclusion_status": "included_pending_source_verification",
        "exclusion_reason": "", "selection_rank": str(rank), "selection_hash": digest,
    }


def build() -> dict[str, int]:
    candidates = list(csv.DictReader(CANDIDATES.open()))
    if len({row["stable_id"] for row in candidates}) != len(candidates):
        raise ValueError("candidate stable_id values must be unique")
    selected = []
    for stratum in sorted({row["stratum"] for row in candidates}):
        members = sorted((selection_hash(row["stable_id"]), row)
                         for row in candidates if row["stratum"] == stratum)
        if len(members) < QUOTA:
            raise ValueError(f"insufficient candidates in {stratum}")
        selected.extend((rank, digest, row) for rank, (digest, row) in enumerate(members[:QUOTA], 1))
    if len(selected) != 100:
        raise ValueError("v2 cohort must contain exactly 100 companies")

    development = []
    v1_rows = list(csv.DictReader((ROOT / "data/restructuring/pre_cutoff_evidence.csv").open()))
    selected_by_ticker = {row["ticker"]: (rank, digest, row) for rank, digest, row in selected}
    for source in v1_rows:
        rank, digest, company = selected_by_ticker.get(source["ticker"], (0, "v1-development", {
            "company": source["company"], "ticker": source["ticker"], "stable_id": f"v1-{source['ticker'].lower()}",
            "sector": "v1 feasibility", "stratum": "development_only"}))
        window_end = "2022-12-31" if source["cutoff"] == "2021-12-31" else "2023-12-31"
        development.append(occasion(company, source["cutoff"], window_end, "development", rank, digest))

    validation = []
    holdout = []
    for rank, digest, row in sorted(selected, key=lambda item: item[2]["stable_id"]):
        validation.append(occasion(row, "2020-12-31", "2021-12-31", "validation", rank, digest))
        if row["ticker"] not in V1_TICKERS:
            validation.append(occasion(row, "2022-12-31", "2023-12-31", "validation", rank, digest))
        holdout.append(occasion(row, "2024-12-31", "2025-12-31", "holdout", rank, digest))
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    write_manifest("restructuring_development.csv", development)
    write_manifest("restructuring_validation.csv", validation)
    write_manifest("restructuring_holdout.csv", holdout)
    result = {"development": len(development), "validation": len(validation), "holdout": len(holdout)}
    print(result)
    return result


if __name__ == "__main__":
    build()

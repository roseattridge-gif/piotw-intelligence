from __future__ import annotations

from collections import defaultdict
from typing import Any


def canonical_event_key(row: dict[str, str]) -> tuple[str, str, str]:
    """Repeated disclosures of one programme map to one parent/date/description key."""
    parent = row["parent_entity"].strip().casefold()
    date = row["public_date"].strip()
    description = " ".join(row["event_description"].casefold().split())
    return parent, date, description


def deduplicate_candidate_events(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    result = []
    for row in rows:
        key = canonical_event_key(row)
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def listed_parent_for_event(row: dict[str, str], entity_map: dict[str, str]) -> str:
    affected = row["affected_entity"].strip().casefold()
    if affected not in entity_map:
        raise ValueError("affected entity has no frozen listed-parent mapping")
    mapped = entity_map[affected]
    declared = row["parent_entity"].strip()
    if mapped != declared:
        raise ValueError("candidate event parent conflicts with frozen entity map")
    return mapped


def agreement_report(first: list[dict[str, str]], second: list[dict[str, str]]) -> dict[str, Any]:
    first_by_id = {row["occasion_id"]: row for row in first if row.get("occasion_id")}
    second_by_id = {row["occasion_id"]: row for row in second if row.get("occasion_id")}
    common = sorted(set(first_by_id) & set(second_by_id))
    agreements = [item for item in common
                  if first_by_id[item]["adjudication"] == second_by_id[item]["adjudication"]]
    disagreements = [
        {"occasion_id": item, "reviewer_1": first_by_id[item]["adjudication"],
         "reviewer_2": second_by_id[item]["adjudication"]}
        for item in common if item not in agreements
    ]
    labels = sorted({row["adjudication"] for row in first_by_id.values()}
                    | {row["adjudication"] for row in second_by_id.values()})
    matrix = defaultdict(int)
    for item in common:
        matrix[(first_by_id[item]["adjudication"], second_by_id[item]["adjudication"])] += 1
    return {
        "reviewer_1_count": len(first_by_id), "reviewer_2_count": len(second_by_id),
        "common_count": len(common), "agreement_count": len(agreements),
        "raw_agreement": len(agreements) / len(common) if common else None,
        "labels": labels,
        "confusion": {f"{left}|{right}": matrix[(left, right)] for left in labels for right in labels},
        "disagreements": disagreements,
    }

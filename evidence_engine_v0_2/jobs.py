from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class TrackedJob:
    identity: str
    title: str
    location: str | None
    status: str = "open"
    consecutive_misses: int = 0
    repost_of: str | None = None


def normalize_location(location: str | None) -> str | None:
    if not location:
        return None
    value = " ".join(location.replace("–", "-").split()).strip(" ,")
    aliases = {"new york city": "New York, NY", "new york": "New York, NY",
               "london, united kingdom": "London, UK", "remote - us": "Remote, US"}
    return aliases.get(value.lower(), value)


def update_job_states(previous: list[TrackedJob], observed: list[TrackedJob], *,
                      collection_success: bool, minimum_consecutive_misses: int = 2,
                      outage_drop_fraction: float = 0.8) -> tuple[list[TrackedJob], dict]:
    """Never close jobs on a failed or suspiciously empty collection."""
    previous_open = [job for job in previous if job.status == "open"]
    if not collection_success:
        return previous, {"healthy": False, "reason": "fetch_failed", "closures_confirmed": 0}
    drop = 1 - len(observed) / len(previous_open) if previous_open else 0
    if len(previous_open) >= 5 and drop >= outage_drop_fraction:
        return previous, {"healthy": False, "reason": "suspected_source_outage", "closures_confirmed": 0}
    observed_by_id = {job.identity: job for job in observed}
    previous_by_id = {job.identity: job for job in previous}
    output = []
    closures = 0
    for identity, old in previous_by_id.items():
        if identity in observed_by_id:
            current = observed_by_id.pop(identity)
            current.consecutive_misses = 0
            current.status = "open"
            output.append(current)
        elif old.status == "open":
            old.consecutive_misses += 1
            if old.consecutive_misses >= minimum_consecutive_misses:
                old.status = "closed"
                closures += 1
            output.append(old)
        else:
            output.append(old)
    closed_signatures = {(re.sub(r"\W+", " ", job.title.lower()).strip(), normalize_location(job.location)): job
                         for job in output if job.status == "closed"}
    for current in observed_by_id.values():
        signature = (re.sub(r"\W+", " ", current.title.lower()).strip(), normalize_location(current.location))
        if signature in closed_signatures:
            current.repost_of = closed_signatures[signature].identity
        output.append(current)
    return sorted(output, key=lambda job: job.identity), {
        "healthy": True, "reason": "ok", "closures_confirmed": closures,
        "observed_count": len(observed), "previous_open_count": len(previous_open),
    }


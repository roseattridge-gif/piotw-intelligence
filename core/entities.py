from __future__ import annotations

import re
from dataclasses import dataclass


def normalize_name(value: str) -> str:
    value = value.casefold().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    suffixes = {"plc", "limited", "ltd", "holdings", "group", "the"}
    return " ".join(token for token in value.split() if token not in suffixes)


@dataclass(frozen=True)
class EntityMatch:
    company_id: str | None
    confidence: float
    method: str


class EntityResolver:
    version = "entity-resolver-0.1.0"

    def __init__(self, aliases: dict[str, str]):
        self.aliases = {normalize_name(alias): company_id for alias, company_id in aliases.items()}

    def resolve(self, value: str) -> EntityMatch:
        normalized = normalize_name(value)
        company_id = self.aliases.get(normalized)
        return EntityMatch(company_id, 1.0 if company_id else 0.0,
                           "exact_normalized_alias" if company_id else "unresolved")

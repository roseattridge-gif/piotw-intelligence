from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from pipelines.common.http import PublicHttpClient


@dataclass(frozen=True)
class ProcurementRecord:
    source_record_id: str
    source_family: str
    notice_id: str
    publication_date: str | None
    buyer: str | None
    supplier_raw_name: str | None
    value: float | None
    currency: str | None
    category: str | None
    description: str | None
    status: str | None
    contract_start: str | None
    contract_end: str | None
    source_url: str
    raw_payload: dict[str, Any]
    content_hash: str
    collector_version: str = "find-a-tender-ocds-v1"


@dataclass(frozen=True)
class SupplierResolution:
    raw_supplier_name: str
    normalized_supplier_name: str
    candidate_company_id: str | None
    match_method: str
    match_confidence: float
    manual_review: bool


def normalize_name(name: str) -> str:
    value = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    return re.sub(r"\b(?:plc|limited|ltd|inc|incorporated|llc|corp|corporation|company|co)\b", "", value).strip()


def resolve_supplier(raw_name: str, company_aliases: dict[str, list[str]]) -> SupplierResolution:
    normalized = normalize_name(raw_name)
    exact = [(company_id, alias) for company_id, aliases in company_aliases.items()
             for alias in aliases if normalize_name(alias) == normalized]
    if len({row[0] for row in exact}) == 1:
        return SupplierResolution(raw_name, normalized, exact[0][0], "normalized_exact_alias", 1.0, False)
    return SupplierResolution(raw_name, normalized, None, "unresolved", 0.0, True)


class FindATenderAdapter:
    source_family = "contracts_procurement"
    base_url = "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages"

    def __init__(self, client: PublicHttpClient | None = None):
        self.client = client or PublicHttpClient()

    def collect(self, published_from: date, published_to: date, limit: int = 100) -> list[ProcurementRecord]:
        url = (f"{self.base_url}?updatedFrom={published_from.isoformat()}T00:00:00"
               f"&updatedTo={published_to.isoformat()}T23:59:59&limit={limit}")
        return self.parse_package(self.client.get_json(url), source_url=url)

    @staticmethod
    def parse_package(payload: dict[str, Any], *, source_url: str) -> list[ProcurementRecord]:
        records = []
        for release in payload.get("releases", []):
            parties = {party.get("id"): party for party in release.get("parties", [])}
            buyer = (release.get("buyer") or {}).get("name")
            awards = release.get("awards") or [None]
            for award in awards:
                award = award or {}
                suppliers = award.get("suppliers") or [None]
                for supplier in suppliers:
                    supplier = supplier or {}
                    supplier_name = supplier.get("name") or (parties.get(supplier.get("id")) or {}).get("name")
                    value = award.get("value") or (release.get("tender") or {}).get("value") or {}
                    period = award.get("contractPeriod") or {}
                    notice_id = str(release.get("id") or release.get("ocid") or "unknown")
                    raw = {"release": release, "award": award, "supplier": supplier}
                    digest = hashlib.sha256(json.dumps(raw, sort_keys=True, default=str).encode()).hexdigest()
                    records.append(ProcurementRecord(
                        source_record_id=f"fts-{hashlib.sha256(f'{notice_id}|{supplier_name}|{digest}'.encode()).hexdigest()[:24]}",
                        source_family="contracts_procurement", notice_id=notice_id,
                        publication_date=release.get("date"), buyer=buyer, supplier_raw_name=supplier_name,
                        value=float(value["amount"]) if value.get("amount") is not None else None,
                        currency=value.get("currency"), category=(release.get("tender") or {}).get("mainProcurementCategory"),
                        description=award.get("description") or (release.get("tender") or {}).get("description"),
                        status=award.get("status") or release.get("tag", [None])[0],
                        contract_start=period.get("startDate"), contract_end=period.get("endDate"),
                        source_url=source_url, raw_payload=raw, content_hash=digest,
                    ))
        return records

from __future__ import annotations

import base64
from urllib.parse import quote, urlencode

from pipelines.common.http import PublicHttpClient


class CompaniesHouseClient:
    """Official public company records. The free API key belongs in the environment."""

    base_url = "https://api.company-information.service.gov.uk"

    def __init__(self, api_key: str, client: PublicHttpClient | None = None):
        if not api_key:
            raise ValueError("A Companies House API key is required")
        self.client = client or PublicHttpClient()
        token = base64.b64encode(f"{api_key}:".encode()).decode()
        self.headers = {"Authorization": f"Basic {token}"}

    def company(self, company_number: str) -> object:
        return self.client.get_json(f"{self.base_url}/company/{quote(company_number)}", self.headers)

    def filing_history(self, company_number: str, items_per_page: int = 100) -> object:
        query = urlencode({"items_per_page": min(items_per_page, 100)})
        return self.client.get_json(
            f"{self.base_url}/company/{quote(company_number)}/filing-history?{query}", self.headers
        )

    def officers(self, company_number: str, items_per_page: int = 100) -> object:
        query = urlencode({"items_per_page": min(items_per_page, 100)})
        return self.client.get_json(
            f"{self.base_url}/company/{quote(company_number)}/officers?{query}", self.headers
        )


class OnsClient:
    """Open, unrestricted ONS beta catalogue and dataset client."""

    base_url = "https://api.beta.ons.gov.uk/v1"

    def __init__(self, client: PublicHttpClient | None = None):
        self.client = client or PublicHttpClient()

    def datasets(self, limit: int = 20, offset: int = 0) -> object:
        return self.client.get_json(f"{self.base_url}/datasets?{urlencode({'limit': limit, 'offset': offset})}")

    def latest_version(self, dataset_id: str, edition: str = "time-series") -> object:
        return self.client.get_json(
            f"{self.base_url}/datasets/{quote(dataset_id)}/editions/{quote(edition)}/versions/latest"
        )


class ContractsFinderClient:
    """Unauthenticated read access to published UK contract notices in OCDS form."""

    base_url = "https://www.contractsfinder.service.gov.uk/Published"

    def __init__(self, client: PublicHttpClient | None = None):
        self.client = client or PublicHttpClient()

    def published_notices(self, published_from: str, published_to: str, limit: int = 100,
                          cursor: str | None = None) -> object:
        params = {"publishedFrom": published_from, "publishedTo": published_to,
                  "limit": min(limit, 100)}
        if cursor:
            params["cursor"] = cursor
        return self.client.get_json(f"{self.base_url}/Notices/OCDS/Search?{urlencode(params)}")


class SecEdgarClient:
    """No-key access to SEC submissions and XBRL company facts for US-listed coverage."""

    base_url = "https://data.sec.gov"

    def __init__(self, contact_user_agent: str, client: PublicHttpClient | None = None):
        if "@" not in contact_user_agent:
            raise ValueError("SEC requests need a descriptive user agent containing a contact email")
        self.client = client or PublicHttpClient(user_agent=contact_user_agent)

    @staticmethod
    def _cik(cik: str | int) -> str:
        return str(cik).zfill(10)

    def submissions(self, cik: str | int) -> object:
        return self.client.get_json(f"{self.base_url}/submissions/CIK{self._cik(cik)}.json")

    def company_facts(self, cik: str | int) -> object:
        return self.client.get_json(f"{self.base_url}/api/xbrl/companyfacts/CIK{self._cik(cik)}.json")

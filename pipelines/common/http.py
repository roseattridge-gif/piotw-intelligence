from __future__ import annotations

import json
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pipelines.common.adapter import SourceUnavailable


@dataclass
class PublicHttpClient:
    """Small, dependency-free client for low-volume public-data collection."""

    user_agent: str = "PIOTW-Research/0.2 (+public-data; contact=operator)"
    timeout_seconds: int = 20
    minimum_interval_seconds: float = 0.5
    retries: int = 2
    _last_request: float = 0.0

    def get_json(self, url: str, headers: dict[str, str] | None = None) -> object:
        return json.loads(self.get_text(url, headers))

    def get_text(self, url: str, headers: dict[str, str] | None = None) -> str:
        if not url.startswith("https://"):
            raise ValueError("Public collectors require HTTPS")
        delay = self.minimum_interval_seconds - (time.monotonic() - self._last_request)
        if delay > 0:
            time.sleep(delay)
        request_headers = {"Accept": "application/json", "User-Agent": self.user_agent}
        request_headers.update(headers or {})
        request = Request(url, headers=request_headers)
        for attempt in range(self.retries + 1):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    self._last_request = time.monotonic()
                    charset = response.headers.get_content_charset() or "utf-8"
                    return response.read().decode(charset, errors="replace")
            except HTTPError as exc:
                if exc.code not in {429, 500, 502, 503, 504} or attempt == self.retries:
                    raise SourceUnavailable(f"GET failed ({exc.code}) for {url}") from exc
            except (URLError, TimeoutError, UnicodeDecodeError) as exc:
                if attempt == self.retries:
                    raise SourceUnavailable(f"GET failed for {url}: {exc}") from exc
            time.sleep(2**attempt)
        raise SourceUnavailable(f"GET failed for {url}")

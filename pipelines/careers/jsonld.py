from __future__ import annotations

import json
from html.parser import HTMLParser


class _JsonLdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_jsonld = False
        self.buffer: list[str] = []
        self.blocks: list[object] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag.lower() == "script" and attributes.get("type", "").lower() == "application/ld+json":
            self.in_jsonld = True
            self.buffer = []

    def handle_data(self, data: str) -> None:
        if self.in_jsonld:
            self.buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self.in_jsonld:
            try:
                self.blocks.append(json.loads("".join(self.buffer)))
            except json.JSONDecodeError:
                pass
            self.in_jsonld = False


def extract_job_postings(html: str) -> list[dict]:
    """Extract schema.org JobPosting records from an already-retrieved public page."""
    parser = _JsonLdParser()
    parser.feed(html)
    found: list[dict] = []

    def visit(value: object) -> None:
        if isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, dict):
            kind = value.get("@type")
            if kind == "JobPosting" or isinstance(kind, list) and "JobPosting" in kind:
                found.append(value)
            if "@graph" in value:
                visit(value["@graph"])

    for block in parser.blocks:
        visit(block)
    return found

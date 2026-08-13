from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime
from intelligence.models import Document

class SourceUnavailable(RuntimeError):
    pass

class SourceAdapter(ABC):
    name: str
    @abstractmethod
    def collect(self, company_id: str, since: datetime | None = None) -> Iterable[Document]: ...

class EvidenceExtractor(ABC):
    @abstractmethod
    def extract(self, document: Document) -> list[dict]: ...

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from intelligence.models import Document

@dataclass(frozen=True)
class BacktestSnapshot:
    prediction_date: datetime
    model_version: str
    documents: tuple[Document, ...]

def freeze_snapshot(documents: list[Document], prediction_date: datetime, model_version: str) -> BacktestSnapshot:
    eligible = tuple(d for d in documents if d.available_at <= prediction_date)
    return BacktestSnapshot(prediction_date, model_version, eligible)

class BacktestModel(Protocol):
    version: str
    def predict(self, snapshot: BacktestSnapshot) -> list[dict]: ...

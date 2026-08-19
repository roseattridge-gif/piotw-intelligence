from __future__ import annotations

from .models import AtomicObservation, EvidenceZone
from .semantic import SemanticObservationProvider
from .validator import validate_semantic_observation


class ObservationEngine:
    def __init__(self, provider: SemanticObservationProvider):
        self.provider = provider

    def extract(self, zones: list[EvidenceZone]) -> list[AtomicObservation]:
        return [validate_semantic_observation(zone, self.provider.extract(zone)) for zone in zones]

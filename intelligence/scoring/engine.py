from intelligence.models import ScoreComponent, ScoreResult

class WeightedEvidenceScorer:
    """Transparent, deterministic v0.1 score; an LLM never selects the result."""
    version = "score-0.1.0"

    def score(self, components: list[ScoreComponent]) -> ScoreResult:
        if not components:
            return ScoreResult(score=50, confidence=0, components=[], model_version=self.version)
        signed = sum(item.contribution for item in components)
        score = round(max(0.0, min(100.0, 50 + signed * 50)))
        independent_mass = sum(item.strength * item.independence for item in components)
        source_quality = sum(item.source_reliability for item in components) / len(components)
        confidence = round(min(100.0, 100 * source_quality * (1 - 1 / (1 + independent_mass))))
        return ScoreResult(score=score, confidence=confidence, components=components, model_version=self.version)

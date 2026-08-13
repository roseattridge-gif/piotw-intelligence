from uuid import uuid4
from intelligence.models import ScoreComponent
from intelligence.scoring.engine import WeightedEvidenceScorer

def test_score_is_reconstructable_and_bounded():
    component = ScoreComponent(signal_id=uuid4(), strength=.8, source_reliability=1, materiality=.75, recency=.9, independence=.5, relevance=1)
    result = WeightedEvidenceScorer().score([component])
    assert result.score == 64
    assert 0 <= result.confidence <= 100
    assert result.components[0].contribution == .27

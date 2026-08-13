from datetime import datetime, timezone
from uuid import uuid4
from backtesting.protocol import freeze_snapshot
from intelligence.models import Document

def doc(available):
    return Document(document_id=uuid4(), company_id=uuid4(), source_id=uuid4(), source_url="https://example.test/a", title="Report", published_at=available, available_at=available, retrieved_at=datetime(2025,1,1,tzinfo=timezone.utc), content_hash="abc", mime_type="application/pdf", parser_version="1")

def test_future_information_is_excluded():
    cutoff=datetime(2021,12,31,tzinfo=timezone.utc)
    snapshot=freeze_snapshot([doc(datetime(2021,1,1,tzinfo=timezone.utc)), doc(datetime(2022,1,1,tzinfo=timezone.utc))], cutoff, "0.1")
    assert len(snapshot.documents) == 1

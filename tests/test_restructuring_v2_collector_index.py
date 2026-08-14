from __future__ import annotations

import json

import scripts.collect_restructuring_v2_reports as collector


def test_record_source_merges_with_fresh_index_state(tmp_path, monkeypatch):
    index = tmp_path / "index.json"
    lock = tmp_path / "index.lock"
    index.write_text(json.dumps({"schema_version": "1", "sources": {"newer": {"status": "preserved"}}}))
    monkeypatch.setattr(collector, "INDEX", index)
    monkeypatch.setattr(collector, "INDEX_LOCK", lock)
    collector.record_source("older-worker-result", {"status": "retrieval_failed"})
    sources = json.loads(index.read_text())["sources"]
    assert sources["newer"]["status"] == "preserved"
    assert sources["older-worker-result"]["status"] == "retrieval_failed"


def test_record_source_never_downgrades_preserved_source(tmp_path, monkeypatch):
    index = tmp_path / "index.json"
    lock = tmp_path / "index.lock"
    index.write_text(json.dumps({
        "schema_version": "1", "sources": {"occasion": {"status": "preserved", "raw_sha256": "abc"}}
    }))
    monkeypatch.setattr(collector, "INDEX", index)
    monkeypatch.setattr(collector, "INDEX_LOCK", lock)
    collector.record_source("occasion", {"status": "retrieval_failed"})
    assert json.loads(index.read_text())["sources"]["occasion"] == {
        "status": "preserved", "raw_sha256": "abc"
    }

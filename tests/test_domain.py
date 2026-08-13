import sqlite3
from datetime import date, datetime, timezone

from core.database import Database
from core.entities import EntityResolver, normalize_name
from core.events import EventCandidate, same_event
from core.predictions import PredictionRegistry, TargetContribution, evidence_snapshot_hash


def test_entity_resolution_is_exact_and_auditable():
    resolver = EntityResolver({"Rolls-Royce Holdings plc": "rolls-royce", "RR.": "rolls-royce"})
    assert normalize_name("Rolls–Royce Holdings PLC") == "rolls royce"
    assert resolver.resolve("Rolls-Royce").company_id == "rolls-royce"
    assert resolver.resolve("Rolls-Rice").company_id is None


def test_event_dedup_requires_company_type_time_and_similarity():
    left = EventCandidate("acme", "site_closure", date(2024, 1, 2), "Closure of Leeds production site")
    right = EventCandidate("acme", "site_closure", date(2024, 1, 8), "Leeds production site closure")
    unrelated = EventCandidate("acme", "contract_win", date(2024, 1, 8), "Leeds production site closure")
    assert same_event(left, right)
    assert not same_event(left, unrelated)


def test_snapshot_hash_is_order_invariant():
    assert evidence_snapshot_hash(["b", "a"], {"x": 1}) == evidence_snapshot_hash(["a", "b"], {"x": 1})


def test_prediction_rows_are_immutable(tmp_path):
    database = Database(tmp_path / "mvp.db")
    database.migrate("database/sqlite")
    with database.connect() as connection:
        connection.execute("INSERT INTO companies VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                           ("acme", "Acme plc", "Acme", None, None, None, None, None, None, "1", "2024-01-01"))
        connection.execute("INSERT INTO sources VALUES(?,?,?,?,?,?,?,?)",
                           ("source", "test", "Test", None, "fixture", 1, None, "{}"))
        connection.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           ("e1", "acme", "source", "1", "https://example.test", "2024-01-01", "2024-01-01",
                            "2024-01-01", "2024-01-01", "Evidence", "Evidence", "{}", "{}", "hash", None,
                            "1", "fixture", 1, 1))
        connection.execute("INSERT INTO model_versions VALUES(?,?,?,?,?,?,?,?,?)",
                           ("model", "rules", "restructuring_announced", "features", "{}", "hash", None,
                            "2024-01-01", "frozen"))
        registry = PredictionRegistry(connection)
        prediction_id = registry.register("acme", "restructuring_announced",
            datetime(2024, 1, 1, tzinfo=timezone.utc), "model", {"x": 1},
            [TargetContribution("e1", None, "supports", 0.2, "Evidence")], 0.4,
            datetime(2024, 1, 1, tzinfo=timezone.utc))
        try:
            connection.execute("UPDATE predictions SET probability=1 WHERE prediction_id=?", (prediction_id,))
        except sqlite3.IntegrityError as exc:
            assert "immutable" in str(exc)
        else:
            raise AssertionError("prediction update was allowed")

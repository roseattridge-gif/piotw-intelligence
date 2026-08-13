import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_twenty_predictions_are_frozen_without_future_evidence():
    subprocess.run([sys.executable, str(ROOT / "scripts/register_restructuring_predictions.py")], check=True)
    result = json.loads((ROOT / "data/derived/restructuring_predictions_pre_outcome.json").read_text())
    assert result["status"] == "frozen before outcome inspection"
    assert result["prediction_count"] == 20
    assert len({(p["ticker"], p["information_cutoff"]) for p in result["predictions"]}) == 20
    with sqlite3.connect(ROOT / "data/derived/restructuring_validation.sqlite3") as connection:
        assert connection.execute("SELECT count(*) FROM evidence WHERE available_at > cutoff").fetchone()[0] == 0
        prediction_id = connection.execute("SELECT prediction_id FROM predictions LIMIT 1").fetchone()[0]
        try:
            connection.execute("UPDATE predictions SET probability=0 WHERE prediction_id=?", (prediction_id,))
        except sqlite3.IntegrityError as error:
            assert "immutable" in str(error)
        else:
            raise AssertionError("prediction update unexpectedly succeeded")


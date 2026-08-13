CREATE TABLE IF NOT EXISTS prediction_resolutions (
  prediction_id TEXT PRIMARY KEY REFERENCES predictions(prediction_id),
  outcome_id TEXT NOT NULL REFERENCES outcomes(outcome_id),
  resolution_status TEXT NOT NULL,
  resolved_at TEXT NOT NULL,
  resolver_version TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS prediction_resolutions_no_update
BEFORE UPDATE ON prediction_resolutions BEGIN SELECT RAISE(ABORT, 'prediction resolutions are immutable'); END;
CREATE TRIGGER IF NOT EXISTS prediction_resolutions_no_delete
BEFORE DELETE ON prediction_resolutions BEGIN SELECT RAISE(ABORT, 'prediction resolutions are immutable'); END;

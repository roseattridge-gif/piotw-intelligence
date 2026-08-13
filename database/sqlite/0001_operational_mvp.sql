PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS companies (
  company_id TEXT PRIMARY KEY,
  legal_name TEXT NOT NULL,
  display_name TEXT NOT NULL,
  companies_house_number TEXT UNIQUE,
  ticker TEXT,
  domain TEXT,
  sector TEXT,
  geography TEXT,
  parent_company_id TEXT REFERENCES companies(company_id),
  entity_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS company_aliases (
  alias_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  alias TEXT NOT NULL,
  normalized_alias TEXT NOT NULL,
  alias_type TEXT NOT NULL,
  confidence REAL NOT NULL CHECK(confidence BETWEEN 0 AND 1),
  valid_from TEXT,
  valid_to TEXT,
  UNIQUE(normalized_alias, company_id)
);
CREATE INDEX IF NOT EXISTS company_alias_lookup_idx ON company_aliases(normalized_alias);

CREATE TABLE IF NOT EXISTS sources (
  source_id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  source_name TEXT NOT NULL,
  base_url TEXT,
  access_mode TEXT NOT NULL,
  reliability_prior REAL NOT NULL CHECK(reliability_prior BETWEEN 0 AND 1),
  terms_checked_at TEXT,
  configuration_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS collector_runs (
  collector_run_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  records_seen INTEGER NOT NULL DEFAULT 0,
  records_created INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,
  collector_version TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence (
  evidence_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  source_record_id TEXT,
  source_url TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  event_date TEXT,
  available_at TEXT NOT NULL,
  collected_at TEXT NOT NULL,
  title TEXT NOT NULL,
  raw_text TEXT,
  structured_value_json TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  content_hash TEXT NOT NULL,
  raw_storage_path TEXT,
  parser_version TEXT NOT NULL,
  extraction_method TEXT NOT NULL,
  extraction_confidence REAL NOT NULL CHECK(extraction_confidence BETWEEN 0 AND 1),
  source_reliability REAL NOT NULL CHECK(source_reliability BETWEEN 0 AND 1),
  UNIQUE(source_id, source_record_id),
  UNIQUE(source_id, content_hash)
);
CREATE INDEX IF NOT EXISTS evidence_company_available_idx ON evidence(company_id, available_at);

CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  event_type TEXT NOT NULL,
  canonical_summary TEXT NOT NULL,
  event_date TEXT NOT NULL,
  earliest_available_at TEXT NOT NULL,
  severity REAL NOT NULL CHECK(severity BETWEEN 0 AND 1),
  resolver_version TEXT NOT NULL,
  fingerprint TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(company_id, event_type, fingerprint)
);
CREATE INDEX IF NOT EXISTS events_company_date_idx ON events(company_id, event_date);

CREATE TABLE IF NOT EXISTS event_evidence (
  event_id TEXT NOT NULL REFERENCES events(event_id),
  evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id),
  relationship TEXT NOT NULL CHECK(relationship IN ('supports','contradicts','context')),
  similarity REAL NOT NULL CHECK(similarity BETWEEN 0 AND 1),
  PRIMARY KEY(event_id, evidence_id)
);

CREATE TABLE IF NOT EXISTS feature_snapshots (
  feature_snapshot_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  feature_name TEXT NOT NULL,
  feature_version TEXT NOT NULL,
  as_of_date TEXT NOT NULL,
  value REAL NOT NULL,
  unit TEXT NOT NULL,
  quality REAL NOT NULL CHECK(quality BETWEEN 0 AND 1),
  evidence_ids_json TEXT NOT NULL,
  calculation_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(company_id, feature_name, feature_version, as_of_date)
);
CREATE INDEX IF NOT EXISTS feature_company_cutoff_idx ON feature_snapshots(company_id, as_of_date);

CREATE TABLE IF NOT EXISTS model_versions (
  model_version TEXT PRIMARY KEY,
  model_type TEXT NOT NULL,
  target TEXT NOT NULL,
  feature_version TEXT NOT NULL,
  configuration_json TEXT NOT NULL,
  configuration_hash TEXT NOT NULL UNIQUE,
  trained_through TEXT,
  created_at TEXT NOT NULL,
  status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS predictions (
  prediction_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  prediction_target TEXT NOT NULL,
  probability REAL NOT NULL CHECK(probability BETWEEN 0 AND 1),
  confidence REAL NOT NULL CHECK(confidence BETWEEN 0 AND 1),
  horizon_months INTEGER NOT NULL CHECK(horizon_months IN (6,12,18)),
  prediction_created_at TEXT NOT NULL,
  information_cutoff_at TEXT NOT NULL,
  model_version TEXT NOT NULL REFERENCES model_versions(model_version),
  feature_values_json TEXT NOT NULL,
  evidence_snapshot_hash TEXT NOT NULL,
  supporting_evidence_json TEXT NOT NULL,
  contradicting_evidence_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  supersedes_prediction_id TEXT REFERENCES predictions(prediction_id),
  UNIQUE(company_id, prediction_target, horizon_months, information_cutoff_at, model_version)
);
CREATE INDEX IF NOT EXISTS predictions_target_cutoff_idx ON predictions(prediction_target, information_cutoff_at);

CREATE TABLE IF NOT EXISTS prediction_evidence (
  prediction_id TEXT NOT NULL REFERENCES predictions(prediction_id),
  evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id),
  event_id TEXT REFERENCES events(event_id),
  relationship TEXT NOT NULL CHECK(relationship IN ('supports','contradicts')),
  contribution REAL NOT NULL,
  PRIMARY KEY(prediction_id, evidence_id)
);

CREATE TABLE IF NOT EXISTS outcomes (
  outcome_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  prediction_target TEXT NOT NULL,
  window_start TEXT NOT NULL,
  window_end TEXT NOT NULL,
  occurred INTEGER NOT NULL CHECK(occurred IN (0,1)),
  outcome_date TEXT,
  resolved_at TEXT NOT NULL,
  resolution_status TEXT NOT NULL,
  resolution_evidence_id TEXT REFERENCES evidence(evidence_id),
  resolver_version TEXT NOT NULL,
  notes TEXT NOT NULL,
  UNIQUE(company_id, prediction_target, window_start, window_end, resolver_version)
);

CREATE TABLE IF NOT EXISTS backtest_runs (
  backtest_run_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  cohort_version TEXT NOT NULL,
  model_version TEXT NOT NULL REFERENCES model_versions(model_version),
  target TEXT NOT NULL,
  configuration_json TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS backtest_results (
  backtest_result_id TEXT PRIMARY KEY,
  backtest_run_id TEXT NOT NULL REFERENCES backtest_runs(backtest_run_id),
  prediction_id TEXT NOT NULL REFERENCES predictions(prediction_id),
  outcome_id TEXT NOT NULL REFERENCES outcomes(outcome_id),
  probability REAL NOT NULL,
  observed INTEGER NOT NULL,
  brier_component REAL NOT NULL,
  lead_time_days INTEGER,
  UNIQUE(backtest_run_id, prediction_id)
);

CREATE TABLE IF NOT EXISTS peer_groups (
  peer_group_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  version TEXT NOT NULL,
  criteria_json TEXT NOT NULL,
  UNIQUE(name, version)
);

CREATE TABLE IF NOT EXISTS peer_group_members (
  peer_group_id TEXT NOT NULL REFERENCES peer_groups(peer_group_id),
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  PRIMARY KEY(peer_group_id, company_id)
);

CREATE TRIGGER IF NOT EXISTS predictions_no_update
BEFORE UPDATE ON predictions BEGIN SELECT RAISE(ABORT, 'predictions are immutable'); END;
CREATE TRIGGER IF NOT EXISTS predictions_no_delete
BEFORE DELETE ON predictions BEGIN SELECT RAISE(ABORT, 'predictions are immutable'); END;
CREATE TRIGGER IF NOT EXISTS prediction_evidence_no_update
BEFORE UPDATE ON prediction_evidence BEGIN SELECT RAISE(ABORT, 'prediction evidence is immutable'); END;
CREATE TRIGGER IF NOT EXISTS prediction_evidence_no_delete
BEFORE DELETE ON prediction_evidence BEGIN SELECT RAISE(ABORT, 'prediction evidence is immutable'); END;

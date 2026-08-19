export interface ValidationPlaceholder { status: "NOT_YET_VALIDATED"; value: null }
export interface Provenance {
  source_family: string; source_url: string | null; source_hash: string | null;
  observed_at: string; effective_at: string | null; collector_version: string;
}
export interface FactualObservation {
  observation_id: string; observation_type: string; state: number | string | null; change: number | null;
  velocity: number | null; novelty: boolean | null; persistence: number | null;
  unit: string | null; validation_status: string; provenance: Provenance[];
}
export interface DimensionView {
  dimension_id: string; name: string; coverage_status: string;
  observations: FactualObservation[]; accepted_events: Record<string, unknown>[];
  score: ValidationPlaceholder;
}
export interface AtomicObservationV037 {
  observation_id: string; company_id: string; source_id: string; source_hash: string;
  source_url: string | null; evidence_span: string; subject: string; action_or_state: string;
  object: string; timing: string; polarity: string; scope: string; entity_relationship: string;
  publication_date: string; confidence: string; decision: "ACCEPT" | "REJECT" | "AMBIGUOUS";
  reason_code: string; extractor_version: string; model_version: string;
}
export interface CareersHistoryPoint {
  observed_at: string; open_roles: number; new_roles: number; persistent_roles: number;
  absent_once_roles: number; confirmed_closed_roles: number; reopened_roles: number;
  source_hash: string; collector_version: string;
}
export interface CompanyIntelligenceSnapshot {
  schema_version: "company-intelligence-snapshot-v1"; company_id: string; display_name: string;
  observation_date: string; dimensions: DimensionView[]; source_freshness: Record<string, unknown>[];
  data_coverage: Record<string, unknown>; prediction: ValidationPlaceholder;
  overall_score: ValidationPlaceholder; benchmark: ValidationPlaceholder;
  pressure: ValidationPlaceholder; expansion: ValidationPlaceholder;
  atomic_observations?: AtomicObservationV037[];
  careers_history?: CareersHistoryPoint[];
}

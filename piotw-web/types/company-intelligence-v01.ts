export type StageStatus = "AVAILABLE" | "WITHHELD" | "NOT_BUILT" | "INSUFFICIENT_EVIDENCE";
export type Confidence = "HIGH" | "MEDIUM" | "LOW" | "NOT_ASSESSED";
export interface IntelligenceEvidence { evidence_id:string; source_id:string; title:string; source_family:string; source_url:string|null; source_hash:string; publication_date:string; information_available_at:string; entity_scope:string; evidence_span:string; collector_or_parser_version:string }
export interface OperationalCondition { condition_id:string; title:string; statement:string; dimension:string; direction:string; materiality:string; evidence_confidence:Confidence; state:string|null; change:string|null; evidence_ids:string[]; caveats:string[] }
export interface ConditionQualification { qualification_id:string; candidate_type:string; status:"QUALIFIED"|"INSUFFICIENT_EVIDENCE"|"WITHHELD"; dimension:string; observation_ids:string[]; evidence_ids:string[]; what_observed:string; why_it_might_matter:string; evidence_strength:string; failed_tests:string[]; missing_information:string[]; what_would_change_view:string; policy_version:string; scientifically_validated:false }
export interface Comparison { comparison_id:string; condition_id:string; status:StageStatus; basis:string; metric:string; target_value:number|null; comparator_value:number|null; gap:number|null; unit:string|null; percentile:number|null; sample_size:number|null; peer_set_or_history:string|null; method:string|null; confidence:Confidence; evidence_ids:string[]; caveats:string[]; withheld_reason:string|null }
export interface PredictiveHypothesis { prediction_id:string; status:StageStatus; target_event:string|null; horizon:string|null; probability:number|null; confidence:Confidence; model_version:string|null; historical_pattern:string|null; supporting_condition_ids:string[]; evidence_ids:string[]; caveats:string[]; withheld_reason:string|null }
export interface Intervention { intervention_id:string; status:StageStatus; title:string|null; mechanism:string|null; investigation_steps:string[]; supporting_condition_ids:string[]; evidence_ids:string[]; evidence_strength:Confidence; falsifiers:string[]; caveats:string[]; withheld_reason:string|null }
export interface FinancialImpact { impact_id:string; intervention_id:string; status:StageStatus; mechanism:string|null; measure:string|null; low:number|null; base:number|null; high:number|null; currency:string|null; unit:string|null; period:string|null; incremental:boolean|null; assumptions:{assumption_id:string;statement:string;value:number;unit:string;basis:string;evidence_ids:string[]}[]; evidence_ids:string[]; caveats:string[]; withheld_reason:string|null }
export interface CompanyIntelligenceV01 {
  schema_version:"piotw-company-intelligence-v0.1";
  company:{company_id:string;display_name:string;legal_name:string|null;ticker:string|null;geography:string|null;activity:string|null};
  as_of:string; generated_at:string; methodology_version:string; scientific_gate_run:false;
  coverage:{status:"HIGH"|"MEDIUM"|"LOW"|"INSUFFICIENT";source_families_present:string[];source_families_missing:string[];evidence_count:number;provenance_complete:boolean;caveats:string[]};
  evidence:IntelligenceEvidence[]; condition_qualifications?:ConditionQualification[]; conditions:OperationalCondition[]; comparisons:Comparison[];
  predictions:PredictiveHypothesis[]; interventions:Intervention[]; financial_impacts:FinancialImpact[];
  capabilities:{detect:StageStatus;compare:StageStatus;predict:StageStatus;prescribe:StageStatus;quantify:StageStatus};
  missing_capabilities:string[]; overall_confidence:Confidence;
}

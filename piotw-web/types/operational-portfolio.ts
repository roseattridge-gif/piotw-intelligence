export type OperationalAttentionItem = {
  company_id: string;
  company_name: string;
  rank: number;
  attention_state: "INVESTIGATE" | "VALIDATE" | "MONITOR";
  observed_change: string;
  direction: string;
  potential_materiality: string;
  evidence_confidence: string;
  urgency: string;
  thesis_relevance: string;
  missing_information: string[];
  validation_question: string;
  capability_status: string;
  company_brief_href: string | null;
  ordering_factors: { note: string; policy_version: string };
};

export type OperationalPortfolioRun = {
  schema_version: "piotw-portfolio-run-v0.1";
  run_id: string;
  portfolio_name: string;
  mode: string;
  synthetic: boolean;
  as_of: string;
  latest_evidence_date: string | null;
  latest_successful_run: string;
  capability_status: string;
  ordering_explanation: string;
  attention_items: OperationalAttentionItem[];
  changes: Array<{ change_type: string; company_id: string | null; statement: string }>;
  operating_review_brief: {
    summary: string;
    top_attention_changes: string[];
    newly_urgent_items: string[];
    source_failures: string[];
    management_validation_questions: string[];
  };
  buyer_test: { questions: string[]; logging: string };
};

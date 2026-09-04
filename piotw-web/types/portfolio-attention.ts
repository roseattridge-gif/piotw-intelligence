export type AttentionState =
  | "Investigate now"
  | "Watch closely"
  | "Validate"
  | "No immediate action"
  | "Pressure easing";

export type ChangeDirection = "Deteriorating" | "Mixed" | "Stable" | "Improving";
export type ChangeVelocity = "Rapid" | "Building" | "Gradual" | "Low";
export type EvidenceConfidence = "High" | "Medium" | "Low";
export type Urgency = "Immediate" | "This week" | "This month" | "Routine";
export type CapabilityState = "AVAILABLE" | "WITHHELD" | "NOT_BUILT" | "NOT_COMPARABLE" | "INSUFFICIENT_EVIDENCE";

export type AttentionReason = {
  label: string;
  kind: "OBSERVATION" | "DERIVED_MEASURE" | "INFERENCE" | "HYPOTHESIS";
  referenceIds: string[];
};

export type CapabilityReference = {
  capability: string;
  state: CapabilityState;
};

export type PortfolioCompanyAttention = {
  id: string;
  name: string;
  operatingModel: string;
  sector: string;
  rank: number;
  attentionState: AttentionState;
  direction: ChangeDirection;
  velocity: ChangeVelocity;
  principalReason: AttentionReason;
  supportingSummary: string;
  changedSince: string;
  potentialImpact: "High" | "Medium" | "Low" | "WITHHELD";
  evidenceConfidence: EvidenceConfidence;
  urgency: Urgency;
  thesisRelevance: string | "UNKNOWN";
  missingInformation: string[];
  validationQuestion: string;
  alternativeExplanation: string;
  nextAction: string;
  capabilities: CapabilityReference[];
  drillDownHref?: string;
};

export type PortfolioAttentionView = {
  id: string;
  label: "Simulated portfolio — product demonstration";
  asOf: string;
  orderingNote: string;
  companies: PortfolioCompanyAttention[];
};

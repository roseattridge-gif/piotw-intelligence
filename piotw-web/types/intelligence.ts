export type Category =
  | "Cost & Efficiency" | "People" | "Capacity" | "Supply Chain"
  | "Restructuring" | "Investment" | "Technology";
export type Confidence = "High" | "Medium" | "Low";
export type ScoreTrend = "Deteriorating" | "Stable" | "Improving";
export type Materiality = "High" | "Medium" | "Low";
export type MethodologyStatus = "Development methodology — not validated";

export interface Company {
  id: string; slug: string; name: string; ticker?: string; sector: string;
  description: string; latestReportingPeriod: string; lastAnalysedAt: string;
  evidenceCoverage: string; operationalBrief: string; story: string[];
}
export interface Document {
  id: string; companyId: string; title: string; type: string;
  reportingPeriod: string; publicationDate: string; pageCount?: number;
  sourceUrl?: string; analysisStatus: "Analysed" | "In review";
  observationCount: number;
}
export interface EvidenceObservation {
  id: string; companyId: string; documentId: string; category: Category;
  observation: string; sourceExcerpt?: string; page?: number;
  confidence?: Confidence; eventDate: string; evidenceType?: string;
  interpretation?: string;
}
export interface OperationalSignal {
  id: string; companyId: string; category: Category; status: string;
  direction?: "Rising" | "Falling" | "Stable" | "Changing";
  confidence?: Confidence; evidenceCount: number; explanation: string;
  supportingEvidenceIds: string[];
}
export interface Interpretation {
  id: string; companyId: string; title: string; summary: string;
  confidence?: Confidence; supportingEvidenceIds: string[];
}
export interface OperationalEvent {
  id: string; companyId: string; date: string; category: Category;
  title: string; description: string; evidenceIds: string[];
  confidence?: Confidence;
}
export interface Prediction {
  id: string; companyId: string; target: string; horizon: string;
  probability: number; confidence?: number; modelVersion: string;
  supportingFeatureIds: string[];
}
export interface EvidenceConfidenceScore {
  score?: number; label: Confidence; explanation?: string;
}
export interface OperationalIndex {
  score: number; rating: string; trend: ScoreTrend; change?: number;
  sectorPercentile?: number; evidenceConfidence: EvidenceConfidenceScore;
  methodologyStatus: MethodologyStatus; outlook?: string;
}
export interface PeerBenchmark {
  name: string; companyPercentile: number; companyScore: number;
  medianScore?: number; lowerQuartile?: number; upperQuartile?: number;
}
export interface OperationalDimensionScore {
  id: string; category: string; score: number; trend: ScoreTrend;
  confidence?: Confidence; evidenceCount?: number; explanation?: string;
  supportingEvidenceIds?: string[];
}
export interface RatingDriver {
  id: string; category: string; rank: number; downsideWeight: number;
  materiality: Materiality; direction: ScoreTrend;
  supportingEvidenceIds: string[]; explanation?: string;
}
export interface FinancialLinkage {
  id: string; operationalCategory: string; financialAreas: string[];
  explanation: string; supportingEvidenceIds: string[]; confidence?: Confidence;
}
export interface InterventionPriority {
  id: string; rank: number; title: string; priority: "Very high" | "High" | "Medium";
  rationale: string[]; interventionClasses: string[]; financialAreas: string[];
  supportingEvidenceIds: string[];
}
export interface CompanyIntelligence {
  company: Company; documents: Document[]; evidence: EvidenceObservation[];
  signals: OperationalSignal[]; interpretations: Interpretation[];
  timeline: OperationalEvent[]; predictions: Prediction[];
  operationalIndex?: OperationalIndex; peerBenchmark?: PeerBenchmark;
  dimensionScores?: OperationalDimensionScore[]; ratingDrivers?: RatingDriver[];
  financialLinkages?: FinancialLinkage[]; interventionPriorities?: InterventionPriority[];
}

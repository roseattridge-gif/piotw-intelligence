import type { EvidenceObservation } from "@/types/intelligence";

export type XRayLayer = "pressure" | "financial" | "volume" | "technology" | "customer" | "data" | "ownership" | "culture";
export type PressureLevel = "healthy" | "watch" | "pressured" | "critical" | "unknown";
export type EvidenceClass = "Observed" | "Strong inference" | "Hypothesis";
export type EvidenceConfidence = "High" | "Medium" | "Low";

export interface XRaySignal {
  id: string;
  title: string;
  detail: string;
  classification: EvidenceClass;
  confidence: EvidenceConfidence;
  date?: string;
  source?: string;
  sourceEvidenceId?: string;
  sourceUrl?: string;
  entityScope?: string;
  canonicalObjectId?: string;
  unknowns?: string[];
}

export interface XRayFinancial {
  label: string;
  range: string;
  mechanism: string;
  estimateBasis: string;
  classification: "Public fact" | "Derived input" | "Scenario output" | "Modelled estimate" | "Withheld";
  evidenceIds?: string[];
  entityScope?: string;
}

export interface XRayTechnology {
  name: string;
  role: string;
  status: EvidenceClass | "Unknown";
  integration: "Low" | "Medium" | "High" | "Unknown";
}

export interface XRayNode {
  id: string;
  name: string;
  description: string;
  pressure: PressureLevel;
  trend: "Improving" | "Stable" | "Deteriorating";
  confidence: EvidenceConfidence;
  materiality: "High" | "Medium" | "Low";
  volume?: { value: string; label: string; basis: "Observed" | "Illustrative estimate"; band?: "low" | "medium" | "high" };
  financials: XRayFinancial[];
  technologies: XRayTechnology[];
  customerSignals: { theme: string; signal: string; status: EvidenceClass; confidence: EvidenceConfidence }[];
  dataMaturity?: { score: number; label: string; dimensions: string[]; status: EvidenceClass };
  ownershipRoles: string[];
  cultureSignals: { signal: string; status: "Weak signal" | "Medium signal"; classification: "Hypothesis" }[];
  signals: XRaySignal[];
  interpretation: string;
  intervention: { title: string; mechanism: string; actions: string[] };
  diligenceQuestions: string[];
  ecommerce?: { id: string; name: string; pressure: PressureLevel; note: string }[];
}

export interface XRayHandoff extends XRayNode {
  from: string;
  to: string;
  accountability: string;
}

export interface CompanyOperationalMap {
  company: { id: string; slug: string; name: string; period: string; archetype: string };
  summary: {
    rating: string;
    percentile: string;
    trend: string;
    valueTrapped: string;
    primaryConstraint: string;
    confidence: EvidenceConfidence;
    thesis: string;
    methodologyStatus: string;
  };
  scores: { label: string; value: string; status: "Live fixture" | "Illustrative demo" }[];
  stages: XRayNode[];
  handoffs: XRayHandoff[];
  hotspots: { id: string; rank: number; targetId: string; relatedIds?: string[]; title: string; pressure: PressureLevel; value: string; confidence: EvidenceConfidence }[];
  causalChains: { id: string; title: string; nodes: string[]; classification: EvidenceClass }[];
  sourceEvidence: EvidenceObservation[];
  dataMode?: "DEVELOPMENT_FIXTURE" | "REAL_COMPANY";
  entityScope?: { primary:string; included:string[]; excluded:string[]; note:string };
  coverageRows?: { row:XRayLayer|"value-stream"; state:"LIVE / SOURCE-BACKED"|"DERIVED / DEVELOPMENT"|"PARTIAL"|"UNAVAILABLE"|"WITHHELD"; sourceFamilies:string[]; missingSource:string; note:string }[];
}

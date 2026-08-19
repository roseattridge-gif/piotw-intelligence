export type Direction = "Improving" | "Stable" | "Weakening";
export type NorthStarDimension = {
  id: string; name: string; score: number; state: string; direction: Direction;
  percentile: number; confidence: "High" | "Medium" | "Low"; driver: string;
  change: string; observation: string; evidenceId: string;
};
export type NorthStarEvidence = {
  id: string; source: string; date: string; observation: string; excerpt: string;
};
export type NorthStarCompany = {
  synthetic: true; id: string; name: string; sector: string; peerGroup: string;
  rating: number; priorRating: number; state: string; percentile: number;
  confidence: "High" | "Medium" | "Low"; coverage: string; summary: string;
  whyItMatters: string; pressure: number; expansion: number;
  dimensions: NorthStarDimension[];
  events: { name: string; sixMonth: number; twelveMonth: number; trend: Direction; peerPrior: number; contributors: string[]; confidence: string }[];
  finance: { operational: string; financial: string; implication: string }[];
  diligence: string[];
  timeline: { period: string; rating: number; note: string }[];
  evidence: NorthStarEvidence[];
};

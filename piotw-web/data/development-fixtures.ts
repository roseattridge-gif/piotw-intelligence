import type { CompanyIntelligence, Category } from "@/types/intelligence";

// DEVELOPMENT-SAFE FIXTURE. Northstar Industrial plc is fictional. None of the
// observations or interpretations below represents real PIOTW analytical output.
const companyId = "northstar";
const categories: Category[] = ["Cost & Efficiency", "People", "Capacity", "Supply Chain", "Restructuring", "Investment", "Technology"];

export const northstarFixture: CompanyIntelligence = {
  company: {
    id: companyId, slug: "northstar-industrial", name: "Northstar Industrial plc",
    ticker: "NST", sector: "Industrial engineering",
    description: "A fictional diversified industrial group used to demonstrate the PIOTW interface.",
    latestReportingPeriod: "FY 2025", lastAnalysedAt: "2026-08-12",
    evidenceCoverage: "High · 4 core disclosures",
    operationalBrief: "Public disclosures indicate a business moving from expansion towards tighter operational control. Evidence suggests that footprint simplification, procurement changes and automation investment are being pursued together, while management continues to describe demand as uneven.",
    story: ["Selective expansion", "Input and delivery pressure", "Simplification", "Footprint restructuring"],
  },
  documents: [
    { id: "d1", companyId, title: "FY 2023 Annual Report", type: "Annual report", reportingPeriod: "FY 2023", publicationDate: "2024-03-14", pageCount: 164, analysisStatus: "Analysed", observationCount: 3 },
    { id: "d2", companyId, title: "2024 Half-year Results", type: "Results statement", reportingPeriod: "H1 2024", publicationDate: "2024-08-01", pageCount: 32, analysisStatus: "Analysed", observationCount: 3 },
    { id: "d3", companyId, title: "FY 2024 Annual Report", type: "Annual report", reportingPeriod: "FY 2024", publicationDate: "2025-03-20", pageCount: 172, analysisStatus: "Analysed", observationCount: 4 },
    { id: "d4", companyId, title: "2025 Capital Markets Update", type: "Investor presentation", reportingPeriod: "FY 2025", publicationDate: "2025-11-06", pageCount: 41, analysisStatus: "Analysed", observationCount: 4 },
  ],
  evidence: [
    ["e1","d1","Capacity","A second assembly line was commissioned at the eastern facility.",24,"High","Facility change"],
    ["e2","d1","Investment","Capital expenditure was directed towards machining and test equipment.",61,"High","Capital allocation"],
    ["e3","d1","People","Specialist engineering recruitment remained difficult in two regions.",38,"Medium","Workforce"],
    ["e4","d2","Supply Chain","Management reported longer inbound lead times for electronic components.",8,"High","Constraint"],
    ["e5","d2","Cost & Efficiency","Freight and expedited delivery costs increased during the period.",11,"High","Cost movement"],
    ["e6","d2","Capacity","Utilisation at the newer line remained below its planned run rate.",14,"Medium","Utilisation"],
    ["e7","d3","Restructuring","The group began consolidating two small service locations into regional hubs.",47,"High","Footprint change"],
    ["e8","d3","Cost & Efficiency","A procurement programme was extended across the group.",52,"High","Efficiency initiative"],
    ["e9","d3","Technology","Automated inspection was introduced at three manufacturing sites.",66,"High","Technology adoption"],
    ["e10","d3","People","Consultation began on roles affected by service-location consolidation.",49,"High","Workforce change"],
    ["e11","d4","Restructuring","Management described the footprint programme as moving into implementation.",17,"High","Programme update"],
    ["e12","d4","Investment","Investment priorities shifted towards automation and existing-site productivity.",21,"High","Capital allocation"],
    ["e13","d4","Technology","A common production-planning platform was scheduled for group-wide deployment.",27,"Medium","Systems change"],
    ["e14","d4","Supply Chain","Dual sourcing had been established for selected constrained components.",31,"Medium","Resilience action"],
  ].map(([id, documentId, category, observation, page, confidence, evidenceType], index) => ({
    id: String(id), companyId, documentId: String(documentId), category: category as Category,
    observation: String(observation), page: Number(page), confidence: confidence as "High" | "Medium",
    evidenceType: String(evidenceType), eventDate: ["2024-03-14","2024-03-14","2024-03-14","2024-08-01","2024-08-01","2024-08-01","2025-03-20","2025-03-20","2025-03-20","2025-03-20","2025-11-06","2025-11-06","2025-11-06","2025-11-06"][index],
    sourceExcerpt: undefined,
    interpretation: index === 6 ? "This observation contributes to the interpretation that simplification has progressed into physical footprint change." : undefined,
  })),
  signals: [
    { id:"s1",companyId,category:"Cost & Efficiency",status:"Elevated",direction:"Rising",confidence:"High",evidenceCount:2,explanation:"Procurement action follows reported logistics pressure.",supportingEvidenceIds:["e5","e8"] },
    { id:"s2",companyId,category:"Restructuring",status:"Active",direction:"Rising",confidence:"High",evidenceCount:3,explanation:"Location consolidation has moved from announcement towards implementation.",supportingEvidenceIds:["e7","e10","e11"] },
    { id:"s3",companyId,category:"Capacity",status:"Changing",direction:"Changing",confidence:"Medium",evidenceCount:2,explanation:"Recent expansion coexists with lower-than-planned utilisation.",supportingEvidenceIds:["e1","e6"] },
    { id:"s4",companyId,category:"Investment",status:"Selective",direction:"Changing",confidence:"High",evidenceCount:3,explanation:"Capital emphasis appears to be moving from expansion to productivity.",supportingEvidenceIds:["e2","e9","e12"] },
  ],
  interpretations: [
    { id:"i1",companyId,title:"Expansion is giving way to utilisation discipline",summary:"Evidence across three reporting periods suggests the operational emphasis has shifted from adding capacity to improving returns from the existing footprint.",confidence:"Medium",supportingEvidenceIds:["e1","e2","e6","e12"] },
    { id:"i2",companyId,title:"Simplification is becoming operational",summary:"Service-location consolidation, related people consultation and subsequent implementation language indicate a programme progressing beyond intent.",confidence:"High",supportingEvidenceIds:["e7","e10","e11"] },
  ],
  timeline: [
    {id:"t1",companyId,date:"2024-03-14",category:"Capacity",title:"New line commissioned",description:"The eastern facility added assembly capacity.",evidenceIds:["e1"],confidence:"High"},
    {id:"t2",companyId,date:"2024-08-01",category:"Supply Chain",title:"Inbound constraints reported",description:"Lead times and expedited freight affected operations.",evidenceIds:["e4","e5"],confidence:"High"},
    {id:"t3",companyId,date:"2024-08-01",category:"Capacity",title:"Utilisation below plan",description:"The newer line had not reached its planned run rate.",evidenceIds:["e6"],confidence:"Medium"},
    {id:"t4",companyId,date:"2025-03-20",category:"Restructuring",title:"Service footprint consolidation",description:"Two service locations were set to move into regional hubs.",evidenceIds:["e7","e10"],confidence:"High"},
    {id:"t5",companyId,date:"2025-03-20",category:"Technology",title:"Automated inspection introduced",description:"Three sites adopted automated inspection.",evidenceIds:["e9"],confidence:"High"},
    {id:"t6",companyId,date:"2025-11-06",category:"Investment",title:"Investment priorities shift",description:"Automation and productivity became the stated priorities.",evidenceIds:["e12","e13"],confidence:"High"},
    {id:"t7",companyId,date:"2025-11-06",category:"Supply Chain",title:"Dual sourcing established",description:"Selected component risks were addressed through a second source.",evidenceIds:["e14"],confidence:"Medium"},
  ],
  // DEVELOPMENT-ONLY / NOT VALIDATED. The values below demonstrate the intended
  // product interface. They were not calculated by the Evidence Engine, trained
  // on peer outcomes, or produced by a validated PIOTW methodology.
  operationalIndex: {
    score: 47, rating: "D", trend: "Deteriorating", change: -8,
    sectorPercentile: 23, outlook: "Deteriorating",
    evidenceConfidence: { score: 86, label: "High", explanation: "Four core disclosures and fourteen source-linked observations are represented in this development fixture." },
    methodologyStatus: "Development methodology — not validated",
  },
  peerBenchmark: {
    name: "Aerospace & Industrial Engineering peers", companyPercentile: 23,
    companyScore: 47, medianScore: 58, lowerQuartile: 49, upperQuartile: 71,
  },
  dimensionScores: [
    { id:"dim-cost",category:"Cost & Efficiency",score:38,trend:"Deteriorating",confidence:"High",evidenceCount:2,explanation:"Cost pressure and procurement action appear together.",supportingEvidenceIds:["e5","e8"] },
    { id:"dim-people",category:"People & Organisation",score:52,trend:"Stable",confidence:"Medium",evidenceCount:2,explanation:"Recruitment pressure coexists with organisation simplification.",supportingEvidenceIds:["e3","e10"] },
    { id:"dim-capacity",category:"Capacity & Footprint",score:43,trend:"Deteriorating",confidence:"High",evidenceCount:4,explanation:"Under-utilisation and footprint consolidation follow earlier expansion.",supportingEvidenceIds:["e1","e6","e7","e11"] },
    { id:"dim-supply",category:"Supply Chain",score:61,trend:"Improving",confidence:"Medium",evidenceCount:2,explanation:"Earlier constraints are followed by selected dual sourcing.",supportingEvidenceIds:["e4","e14"] },
    { id:"dim-tech",category:"Technology & Execution",score:58,trend:"Stable",confidence:"Medium",evidenceCount:2,explanation:"Automation is being introduced while group-wide deployment remains prospective.",supportingEvidenceIds:["e9","e13"] },
    { id:"dim-growth",category:"Growth & Investment",score:67,trend:"Improving",confidence:"High",evidenceCount:3,explanation:"Investment emphasis shifts towards automation and productivity.",supportingEvidenceIds:["e2","e9","e12"] },
  ],
  ratingDrivers: [
    { id:"driver-cost",category:"Cost & Efficiency",rank:1,downsideWeight:31,materiality:"High",direction:"Deteriorating",supportingEvidenceIds:["e5","e8"],explanation:"Reported logistics cost pressure is followed by broader procurement action." },
    { id:"driver-capacity",category:"Capacity & Footprint",rank:2,downsideWeight:24,materiality:"High",direction:"Deteriorating",supportingEvidenceIds:["e1","e6","e7","e11"],explanation:"Expansion, lower utilisation and footprint consolidation form the principal operational sequence." },
    { id:"driver-people",category:"People & Organisation",rank:3,downsideWeight:18,materiality:"Medium",direction:"Stable",supportingEvidenceIds:["e3","e10"],explanation:"Recruitment constraints and consultation create execution considerations." },
  ],
  financialLinkages: [
    { id:"fin-cost",operationalCategory:"Cost & Efficiency",financialAreas:["Gross margin","SG&A","EBITDA margin"],explanation:"Freight cost pressure and procurement activity may be relevant when investigating cost progression.",supportingEvidenceIds:["e5","e8"],confidence:"High" },
    { id:"fin-capacity",operationalCategory:"Capacity & Footprint",financialAreas:["Fixed-cost absorption","Capex efficiency","ROCE","Exceptional restructuring charges"],explanation:"Utilisation and footprint evidence may be relevant to asset productivity and restructuring analysis.",supportingEvidenceIds:["e1","e6","e7","e11"],confidence:"High" },
    { id:"fin-supply",operationalCategory:"Supply Chain",financialAreas:["Working capital","Inventory","COGS","Cash conversion"],explanation:"Lead-time constraints and dual sourcing may be relevant to inventory and cash-conversion investigation.",supportingEvidenceIds:["e4","e14"],confidence:"Medium" },
    { id:"fin-growth",operationalCategory:"Growth & Investment",financialAreas:["Capex","ROIC","Depreciation","Revenue growth"],explanation:"The shift in investment emphasis may be relevant to capital allocation and return analysis.",supportingEvidenceIds:["e2","e9","e12"],confidence:"High" },
  ],
  interventionPriorities: [
    { id:"priority-capacity",rank:1,title:"Capacity & utilisation",priority:"Very high",rationale:["Repeated capacity and footprint observations","Deteriorating development dimension","High evidence confidence","Recent restructuring activity"],interventionClasses:["Capacity utilisation diagnostic","Footprint review","Complexity reduction","Make / buy analysis"],financialAreas:["Gross margin","Fixed-cost absorption","ROCE","Restructuring costs"],supportingEvidenceIds:["e1","e6","e7","e11"] },
    { id:"priority-cost",rank:2,title:"Cost base & efficiency",priority:"High",rationale:["Highest development downside weighting","Logistics cost pressure","Group procurement response"],interventionClasses:["Cost-base diagnostic","Procurement effectiveness review","Complexity reduction"],financialAreas:["Gross margin","SG&A","EBITDA margin"],supportingEvidenceIds:["e5","e8"] },
    { id:"priority-execution",rank:3,title:"Technology execution",priority:"Medium",rationale:["Multi-site automation activity","Group-wide platform deployment remains prospective"],interventionClasses:["Benefits-realisation review","Deployment readiness assessment","Investment productivity review"],financialAreas:["Capex efficiency","ROIC","Operating cost"],supportingEvidenceIds:["e9","e13"] },
  ],
  predictions: [],
};

export const fixtures = [northstarFixture];
export const fixtureCategories = categories;

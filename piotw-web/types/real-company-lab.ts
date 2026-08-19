export type LabEvidenceClass = "PUBLIC_EVIDENCE" | "PIOTW_DERIVATION" | "FOUNDER_RETROSPECTIVE";
export type LabEntity = { id:string; name:string; kind:"GROUP"|"BUSINESS_UNIT"; parentId?:string; status:"IN_SCOPE"|"FUTURE" };
export type LabSource = { id:string; entityId:string; title:string; sourceType:string; publicationDate:string; effectiveDate:string; fetchedAt:string; url:string; rawContent:string; contentHash:string; evidenceClass:"PUBLIC_EVIDENCE" };
export type LabObservation = { id:string; sourceId:string; entityId:string; asOf:string; category:string; fact:string; evidenceSpan:string; dimensions:string[]; evidenceClass:"PUBLIC_EVIDENCE"; scope:string };
export type LabDimension = { id:string; name:string; state:string; movement:string; coverage:"HIGH"|"MEDIUM"|"LOW"|"INSUFFICIENT PUBLIC EVIDENCE"; observationIds:string[]; interpretation:string };
export type LabMetric = { name:string; value:string; prior?:string; basis:string; sourceId:string };
export type LabSnapshot = { asOf:string; label:string; story:string; whatChanged:string; whyItMayMatter:string; illustrativeRating:number; priorRating?:number; prototypePercentile:number; coverage:number; dimensions:LabDimension[]; observationIds:string[]; metrics:LabMetric[]; forwardEvent:{name:string; probability:number; horizon:string; explanation:string} };

import type { AtomicObservationV037, CareersHistoryPoint, CompanyIntelligenceSnapshot } from "../../types/company-intelligence.ts";

export type FactualChangeType =
  | "CAREERS_APPEARED" | "CAREERS_PERSISTED" | "CAREERS_ABSENT_ONCE"
  | "CAREERS_CONFIRMED_CLOSED" | "CAREERS_REOPENED" | "ATOMIC_OBSERVATION"
  | "PROCUREMENT_RELEASE" | "PROCUREMENT_REVISION" | "SOURCE_HEALTH_CHANGE";

export interface IntelligenceChange {
  id: string; company_id: string; company_name: string; date: string;
  type: FactualChangeType; source_family: "careers_ats" | "issuer_document" | "procurement" | "source_health";
  statement: string; why_shown: string; count: number; evidence_span?: string; source_url?: string | null;
  source_id?: string; source_hash?: string; observation_id?: string; version: string;
}
export type IntelligencePeriod = "previous" | "7" | "30" | "all";

const atomicStatement = (item: AtomicObservationV037) => `${item.subject} ${item.action_or_state} ${item.object}.`;
const careerChange = (profile: CompanyIntelligenceSnapshot, point: CareersHistoryPoint, type: FactualChangeType, count: number, statement: string): IntelligenceChange => ({
  id: `${profile.company_id}-${type}-${point.observed_at}`, company_id: profile.company_id, company_name: profile.display_name,
  date: point.observed_at, type, source_family: "careers_ats", statement,
  count,
  why_shown: `Shown because PIOTW recorded ${count} factual careers ${count === 1 ? "change" : "changes"} in this observation.`,
  source_hash: point.source_hash, version: point.collector_version,
});

export function profileChanges(profile: CompanyIntelligenceSnapshot): IntelligenceChange[] {
  const atomic = (profile.atomic_observations ?? []).filter((item) => item.decision === "ACCEPT").map((item): IntelligenceChange => ({
    id: item.observation_id, company_id: profile.company_id, company_name: profile.display_name,
    date: item.publication_date, type: "ATOMIC_OBSERVATION", source_family: "issuer_document",
    count: 1,
    statement: atomicStatement(item), why_shown: "Shown because PIOTW retained an accepted development factual observation with exact supporting evidence.",
    evidence_span: item.evidence_span, source_url: item.source_url, source_id: item.source_id,
    source_hash: item.source_hash, observation_id: item.observation_id, version: item.extractor_version,
  }));
  const careers = (profile.careers_history ?? []).flatMap((point) => {
    const rows: IntelligenceChange[] = [];
    if (point.new_roles) rows.push(careerChange(profile, point, "CAREERS_APPEARED", point.new_roles, point.new_roles === 1 ? "1 role was newly observed." : `${point.new_roles} roles were newly observed.`));
    if (point.persistent_roles) rows.push(careerChange(profile, point, "CAREERS_PERSISTED", point.persistent_roles, `${point.persistent_roles} previously observed roles persisted.`));
    if (point.absent_once_roles) rows.push(careerChange(profile, point, "CAREERS_ABSENT_ONCE", point.absent_once_roles, point.absent_once_roles === 1 ? "1 role was absent once and remains unconfirmed as closed." : `${point.absent_once_roles} roles were absent once and remain unconfirmed as closed.`));
    if (point.confirmed_closed_roles) rows.push(careerChange(profile, point, "CAREERS_CONFIRMED_CLOSED", point.confirmed_closed_roles, `${point.confirmed_closed_roles} roles met the confirmed-closure rule.`));
    if (point.reopened_roles) rows.push(careerChange(profile, point, "CAREERS_REOPENED", point.reopened_roles, point.reopened_roles === 1 ? "1 role reopened." : `${point.reopened_roles} roles reopened.`));
    return rows;
  });
  return [...atomic, ...careers].sort((a, b) => b.date.localeCompare(a.date));
}

export function allChanges(profiles: CompanyIntelligenceSnapshot[]) {
  return profiles.flatMap(profileChanges).sort((a, b) => b.date.localeCompare(a.date));
}

export function sincePreviousChanges(profile: CompanyIntelligenceSnapshot) {
  const history = profile.careers_history ?? []; const latest = history.at(-1); const previous = history.at(-2);
  return profileChanges(profile).filter((item) => item.source_family === "careers_ats" ? Boolean(latest && item.date === latest.observed_at) : !previous || item.date > previous.observed_at);
}

export function filterChangesByPeriod(changes: IntelligenceChange[], period: IntelligencePeriod) {
  if (period === "all" || period === "previous" || !changes.length) return changes;
  const reference = Math.max(...changes.map((item) => new Date(item.date).getTime()));
  const cutoff = reference - Number(period) * 86400000;
  return changes.filter((item) => new Date(item.date).getTime() >= cutoff);
}

export function selectedPeriod(value: string | undefined): IntelligencePeriod {
  return value === "7" || value === "30" || value === "all" ? value : "previous";
}

export function latestEvidenceDate(profile: CompanyIntelligenceSnapshot) {
  return [profile.observation_date, ...(profile.atomic_observations ?? []).map((item) => item.publication_date), ...(profile.careers_history ?? []).map((item) => item.observed_at)].filter(Boolean).sort().at(-1) ?? profile.observation_date;
}

export function acceptedObservationCount(profile: CompanyIntelligenceSnapshot) {
  return (profile.atomic_observations ?? []).filter((item) => item.decision === "ACCEPT").length;
}

export function healthySourceCount(profile: CompanyIntelligenceSnapshot) {
  return profile.source_freshness.filter((source) => String(source.health).toLowerCase() === "healthy").length;
}

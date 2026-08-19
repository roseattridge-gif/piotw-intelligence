import { fixtures } from "../../data/development-fixtures.ts";
import type { CompanyIntelligence } from "../../types/intelligence.ts";

export async function searchCompanies(query = "") {
  const term = query.trim().toLowerCase();
  return fixtures.map((f) => f.company).filter((c) => !term || `${c.name} ${c.ticker ?? ""}`.toLowerCase().includes(term));
}
export async function getCompanyBySlug(slug: string): Promise<CompanyIntelligence | null> {
  return fixtures.find((f) => f.company.slug === slug) ?? null;
}
export async function getCompanyEvidence(slug: string) { return (await getCompanyBySlug(slug))?.evidence ?? []; }
export async function getCompanyTimeline(slug: string) { return (await getCompanyBySlug(slug))?.timeline ?? []; }
export async function getCompanyDocuments(slug: string) { return (await getCompanyBySlug(slug))?.documents ?? []; }

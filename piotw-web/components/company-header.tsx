import type { Company } from "@/types/intelligence";
const formatDate = (value: string) => new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`)).toUpperCase();
export function CompanyHeader({ company }: { company: Company }) {
  return <section className="company-header">
    <div className="company-identity"><p className="eyebrow"><i aria-hidden/> Operational intelligence · updated {formatDate(company.lastAnalysedAt)}</p><div className="company-title-line"><h1>{company.name}</h1>{company.ticker && <span>{company.ticker}</span>}</div><p>{company.sector} <b>•</b> {company.latestReportingPeriod} <b>•</b> {company.evidenceCoverage}</p></div>
  </section>;
}

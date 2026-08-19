import Link from "next/link";
import { ChangeItem } from "@/components/change-item";
import { IntelligenceNav } from "@/components/intelligence-nav";
import { PeriodSelector } from "@/components/period-selector";
import { allChanges, filterChangesByPeriod, selectedPeriod, sincePreviousChanges } from "@/lib/data/intelligence-changes";
import { listCompanyIntelligenceSnapshots } from "@/lib/data/company-intelligence";

const TYPES = ["CAREERS_APPEARED","CAREERS_PERSISTED","CAREERS_ABSENT_ONCE","CAREERS_CONFIRMED_CLOSED","CAREERS_REOPENED","ATOMIC_OBSERVATION"];
export default async function ChangesPage({ searchParams }: { searchParams: Promise<{ company?: string; source?: string; type?: string; period?: string }> }) {
  const query = await searchParams; const profiles = await listCompanyIntelligenceSnapshots(); const period=selectedPeriod(query.period);
  const periodFeed = period === "previous" ? profiles.flatMap(sincePreviousChanges).sort((a,b)=>b.date.localeCompare(a.date)) : filterChangesByPeriod(allChanges(profiles),period);
  const changes = periodFeed.filter((item) => (!query.company || item.company_id === query.company) && (!query.source || item.source_family === query.source) && (!query.type || item.type === query.type));
  return <main className="intelligence-directory change-feed-page"><IntelligenceNav/><header><p className="eyebrow">Cross-company factual feed</p><h1>Recent change</h1><p>Newest factual change first. No importance, risk or predictive meaning is assigned.</p><PeriodSelector period={period}/></header>
    <form className="intelligence-filters"><label>Company<select name="company" defaultValue={query.company ?? ""}><option value="">All companies</option>{profiles.sort((a,b)=>a.display_name.localeCompare(b.display_name)).map((profile)=><option key={profile.company_id} value={profile.company_id}>{profile.display_name}</option>)}</select></label><label>Source family<select name="source" defaultValue={query.source ?? ""}><option value="">All sources</option><option value="careers_ats">Careers / ATS</option><option value="issuer_document">Issuer documents</option></select></label><label>Change type<select name="type" defaultValue={query.type ?? ""}><option value="">All change types</option>{TYPES.map((type)=><option key={type}>{type}</option>)}</select></label><input type="hidden" name="period" value={period}/><button type="submit">Apply factual filters</button></form>
    <section className="cross-company-feed">{changes.length ? changes.map((item)=><ChangeItem key={item.id} item={item}/>) : <p>INSUFFICIENT OBSERVED DATA for these filters.</p>}</section>
    <footer><span>{changes.length} factual feed items · no score · no prediction</span><Link href="/intelligence">← Watchlist</Link></footer></main>;
}

import Link from "next/link";
import { IntelligenceNav } from "@/components/intelligence-nav";
import { listCompanyIntelligenceSnapshots } from "@/lib/data/company-intelligence";
import type { CompanyIntelligenceSnapshot } from "@/types/company-intelligence";

type SortKey = "latest_change" | "latest_evidence" | "freshness" | "observations" | "open_roles" | "company";
const asNumber = (value: unknown) => typeof value === "number" ? value : 0;
const dateOnly = (value: string) => new Intl.DateTimeFormat("en-GB", { dateStyle: "medium" }).format(new Date(value));
function latestDate(profile: CompanyIntelligenceSnapshot) {
  return [profile.observation_date, ...(profile.atomic_observations ?? []).map((item) => item.publication_date), ...(profile.careers_history ?? []).map((item) => item.observed_at)].filter(Boolean).sort().at(-1) ?? profile.observation_date;
}
function latestChangeDate(profile: CompanyIntelligenceSnapshot) {
  const atomicDates = (profile.atomic_observations ?? []).filter((item) => item.decision === "ACCEPT").map((item) => item.publication_date);
  const lifecycleDates = (profile.careers_history ?? []).filter((item) => item.new_roles > 0 || item.absent_once_roles > 0 || item.confirmed_closed_roles > 0 || item.reopened_roles > 0).map((item) => item.observed_at);
  return [...atomicDates, ...lifecycleDates].sort().at(-1) ?? profile.observation_date;
}
function freshestSourceDate(profile: CompanyIntelligenceSnapshot) {
  const sourceDates = profile.source_freshness.flatMap((source) => [source.last_successful_fetch, source.observed_at, source.fetched_at]).filter((value): value is string => typeof value === "string");
  return sourceDates.sort().at(-1) ?? latestDate(profile);
}
function factualObservations(profile: CompanyIntelligenceSnapshot) {
  return (profile.atomic_observations?.filter((item) => item.decision === "ACCEPT").length ?? 0) + profile.dimensions.reduce((total, dimension) => total + dimension.observations.length, 0);
}
function latestSummary(profile: CompanyIntelligenceSnapshot) {
  const atomic = profile.atomic_observations?.filter((item) => item.decision === "ACCEPT").sort((a, b) => b.publication_date.localeCompare(a.publication_date))[0];
  if (atomic) return `${atomic.subject} ${atomic.action_or_state} ${atomic.object}.`;
  const history = profile.careers_history?.at(-1);
  return history ? `${history.open_roles} open roles observed in the latest careers snapshot.` : "No factual observation attached.";
}

export default async function IntelligenceDirectory({ searchParams }: { searchParams: Promise<{ sort?: string; careers?: string; issuer?: string; procurement?: string; health?: string; days?: string }> }) {
  const query = await searchParams; const requested = query.sort;
  const sort: SortKey = ["latest_change", "latest_evidence", "freshness", "observations", "open_roles", "company"].includes(requested ?? "") ? requested as SortKey : "latest_change";
  let profiles = await listCompanyIntelligenceSnapshots();
  const latestRecordedChange = Math.max(...profiles.map((profile) => new Date(latestChangeDate(profile)).getTime()));
  const changedCutoff = query.days && Number.isFinite(Number(query.days)) ? latestRecordedChange - Number(query.days) * 86400000 : null;
  profiles = profiles.filter((profile) => (!query.careers || (profile.careers_history?.length ?? 0) > 0) && (!query.issuer || (profile.atomic_observations?.some((item) => item.decision === "ACCEPT") ?? false)) && (!query.procurement || false) && (!query.health || profile.source_freshness.some((source) => query.health === "healthy" ? String(source.health).toLowerCase() === "healthy" : String(source.health).toLowerCase() !== "healthy")) && (!changedCutoff || new Date(latestChangeDate(profile)).getTime() >= changedCutoff));
  profiles.sort((a, b) => sort === "company" ? a.display_name.localeCompare(b.display_name) : sort === "observations" ? factualObservations(b) - factualObservations(a) : sort === "open_roles" ? asNumber(b.careers_history?.at(-1)?.open_roles) - asNumber(a.careers_history?.at(-1)?.open_roles) : sort === "freshness" ? freshestSourceDate(b).localeCompare(freshestSourceDate(a)) : sort === "latest_evidence" ? latestDate(b).localeCompare(latestDate(a)) : latestChangeDate(b).localeCompare(latestChangeDate(a)));
  return <main className="intelligence-directory watchlist"><IntelligenceNav/>
    <header><p className="eyebrow">Portfolio monitoring · internal product view</p><h1>What changed?</h1><p>A factual watchlist for navigating observable company change. Sorting is a navigation aid—not a risk ranking.</p></header>
    <nav className="watchlist-sort" aria-label="Sort watchlist"><span>Sort by</span>{([['latest_change','Latest change'],['latest_evidence','Latest evidence'],['freshness','Source freshness'],['observations','Most observations'],['open_roles','Open roles'],['company','Company']] as const).map(([key,label]) => <Link key={key} href={`/intelligence?sort=${key}`} aria-current={sort === key ? "page" : undefined}>{label}</Link>)}</nav>
    <form className="intelligence-filters"><label><input type="checkbox" name="careers" value="1" defaultChecked={query.careers === "1"}/> Has careers data</label><label><input type="checkbox" name="issuer" value="1" defaultChecked={query.issuer === "1"}/> Has issuer observations</label><label><input type="checkbox" name="procurement" value="1" defaultChecked={query.procurement === "1"}/> Has resolved procurement</label><label>Source health<select name="health" defaultValue={query.health ?? ""}><option value="">Any state</option><option value="healthy">Has healthy source</option><option value="unhealthy">Has unhealthy source</option></select></label><label>Changed within<select name="days" defaultValue={query.days ?? ""}><option value="">Any time</option><option value="7">7 days</option><option value="30">30 days</option><option value="90">90 days</option></select></label><input type="hidden" name="sort" value={sort}/><button type="submit">Apply navigation filters</button></form>
    <section className="watchlist-table"><header><span>Company</span><span>Latest evidence</span><span>Careers</span><span>Observed change</span><span>Coverage</span></header>{profiles.map((profile) => {
      const history = profile.careers_history ?? []; const current = history.at(-1);
      const sourceFamilies = new Set(profile.source_freshness.map((source) => String(source.source_family))).size;
      const health = profile.source_freshness.map((source) => String(source.health)).join(" · ");
      return <Link key={profile.company_id} href={`/intelligence/${profile.company_id}`}>
        <div><span>{profile.company_id.toUpperCase()}</span><h2>{profile.display_name}</h2><small>{factualObservations(profile)} factual {factualObservations(profile) === 1 ? "observation" : "observations"}</small></div>
        <div><strong>{dateOnly(latestDate(profile))}</strong><small>{health}</small></div>
        <dl><div><dt>Snapshots</dt><dd>{history.length || "—"}</dd></div><div><dt>Open</dt><dd>{current?.open_roles ?? "—"}</dd></div><div><dt>New</dt><dd>{current?.new_roles ?? "—"}</dd></div><div><dt>Absent once</dt><dd>{current?.absent_once_roles ?? "—"}</dd></div></dl>
        <div><p>{latestSummary(profile)}</p><small>Shown because PIOTW recorded {profile.careers_history?.at(-1)?.new_roles ?? 0} new careers observations and {profile.atomic_observations?.filter((item)=>item.decision === "ACCEPT").length ?? 0} accepted issuer observations in the available record.</small></div>
        <div><strong>{sourceFamilies} source {sourceFamilies === 1 ? "family" : "families"}</strong><small>{asNumber(profile.data_coverage.failed_sources) ? "SOURCE ATTENTION NEEDED" : history.length < 3 ? "EARLY LONGITUDINAL HISTORY" : "OBSERVED"}</small></div>
      </Link>;
    })}</section>
    <footer><span>No score · no prediction · no inferred significance</span><Link href="/">← Return to PIOTW</Link></footer>
  </main>;
}

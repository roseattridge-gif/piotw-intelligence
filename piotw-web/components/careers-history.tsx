import type { CareersHistoryPoint } from "@/types/company-intelligence";

function shortDate(value: string) {
  return new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short" }).format(new Date(value));
}

export function CareersHistory({ history }: { history: CareersHistoryPoint[] }) {
  const maximum = Math.max(...history.map((point) => point.open_roles), 1);
  return <section className="careers-history">
    <header><div><p className="eyebrow">Careers history</p><h2>Observed vacancies over time</h2></div><span>EARLY LONGITUDINAL HISTORY</span></header>
    {history.length ? <>
      <div className="careers-chart" role="img" aria-label={`Open roles across ${history.length} careers snapshots`}>
        {history.map((point) => <div key={point.observed_at} className="careers-bar-column">
          <strong>{point.open_roles}</strong><div><i style={{ height: `${Math.max((point.open_roles / maximum) * 100, 3)}%` }} /></div><time>{shortDate(point.observed_at)}</time>
        </div>)}
      </div>
      <div className="careers-history-table"><div className="careers-history-head"><span>Snapshot</span><span>Open</span><span>New</span><span>Persistent</span><span>Absent once</span><span>Closed</span><span>Reopened</span></div>
        {history.map((point) => <div key={`row-${point.observed_at}`}><time>{shortDate(point.observed_at)}</time><strong>{point.open_roles}</strong><span>{point.new_roles}</span><span>{point.persistent_roles}</span><span>{point.absent_once_roles}</span><span>{point.confirmed_closed_roles}</span><span>{point.reopened_roles}</span></div>)}
      </div>
    </> : <p className="truth-empty">No careers snapshots are attached to this company.</p>}
    <p className="truth-method">Counts are factual collection states, not an assessment of company health, growth or risk.</p>
  </section>;
}

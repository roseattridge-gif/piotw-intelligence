import Link from "next/link";
import type { IntelligenceChange } from "@/lib/data/intelligence-changes";

const dateOnly = (value: string) => new Intl.DateTimeFormat("en-GB", { dateStyle: "medium" }).format(new Date(value));
const readable = (value: string) => value.replaceAll("_", " ");

export function ChangeItem({ item, compact = false }: { item: IntelligenceChange; compact?: boolean }) {
  return <article className="change-item">
    <header><time>{dateOnly(item.date)}</time><span>{readable(item.type)}</span></header>
    {!compact ? <Link href={`/intelligence/${item.company_id}`}><strong>{item.company_name}</strong></Link> : null}
    <p>{item.statement}</p><small>{item.why_shown}</small>
    <div className="change-evidence-links">
      {item.evidence_span ? <details><summary>View exact evidence</summary><blockquote>{item.evidence_span}</blockquote></details> : <span>Evidence retained in the immutable collection record</span>}
      {item.source_url ? <a href={item.source_url} target="_blank" rel="noreferrer">Open source ↗</a> : null}
    </div>
    <details className="change-technical"><summary>Technical provenance</summary><dl><div><dt>Observation ID</dt><dd>{item.observation_id ?? "Not applicable"}</dd></div><div><dt>Source ID</dt><dd>{item.source_id ?? "Internal collection record"}</dd></div><div><dt>Source hash</dt><dd>{item.source_hash ?? "Not available"}</dd></div><div><dt>Version</dt><dd>{item.version}</dd></div><div><dt>Timestamp</dt><dd>{item.date}</dd></div></dl></details>
  </article>;
}

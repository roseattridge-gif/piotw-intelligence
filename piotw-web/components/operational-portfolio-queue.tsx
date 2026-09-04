import Link from "next/link";
import type { OperationalPortfolioRun } from "@/types/operational-portfolio";

export function OperationalPortfolioQueue({ run }: { run: OperationalPortfolioRun }) {
  return <div className="op-portfolio">
    <nav className="op-tabs" aria-label="Portfolio views"><Link href="/portfolio">Attention queue</Link><Link href="/portfolio/changes">Changes</Link><Link href="/portfolio/brief">Operating-review brief</Link><Link href="/portfolio/buyer-test">Buyer test</Link><Link href="/portfolio/demo">Synthetic demo</Link></nav>
    <section className="op-summary"><p><strong>Latest successful run</strong>{run.latest_successful_run}</p><p><strong>Evidence through</strong>{run.latest_evidence_date ?? "UNAVAILABLE"}</p><p><strong>Capability</strong>{run.capability_status.replaceAll("_", " ")}</p></section>
    <section aria-labelledby="operational-attention-heading">
      <div className="op-section-head"><div><p className="eyebrow">Operating-team attention</p><h2 id="operational-attention-heading">{run.attention_items.length} companies, ordered transparently.</h2></div><p>{run.ordering_explanation}</p></div>
      <div className="op-attention-list">{run.attention_items.map(item => <article key={item.company_id} className="op-attention-card">
        <header><span className="pa-rank">{String(item.rank).padStart(2, "0")}</span><span className="pa-state">{item.attention_state}</span></header>
        <p className="eyebrow">{item.urgency.replaceAll("_", " ")} · {item.capability_status.replaceAll("_", " ")}</p>
        <h3>{item.company_name}</h3><p className="op-observation">{item.observed_change}</p>
        <dl><div><dt>Potential materiality</dt><dd>{item.potential_materiality}</dd></div><div><dt>Evidence confidence</dt><dd>{item.evidence_confidence}</dd></div><div><dt>Thesis context</dt><dd>{item.thesis_relevance}</dd></div></dl>
        <div className="op-validate"><strong>Validate next</strong><p>{item.validation_question}</p></div>
        <details><summary>Coverage limits and missing information</summary><ul>{item.missing_information.map((value, index) => <li key={`${item.company_id}-${index}`}>{value}</li>)}</ul></details>
        {item.company_brief_href && <Link className="pa-drill" href={item.company_brief_href}>Open evidence-backed company brief <span aria-hidden>↗</span></Link>}
      </article>)}</div>
    </section>
    <aside className="pa-boundary"><strong>Development portfolio boundary</strong><p>Real public-company evidence; development use only. The Datadog source failure is deliberately injected to test failure isolation and is not a claim about the company or its careers site. Unknown is never treated as zero. No probability or investment recommendation is produced.</p></aside>
  </div>;
}

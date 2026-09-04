"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ATTENTION_STATES, DIRECTIONS, filterPortfolioCompanies } from "@/data/portfolio-attention-demo";
import type { PortfolioAttentionView, PortfolioCompanyAttention } from "@/types/portfolio-attention";

function Direction({ company }: { company: PortfolioCompanyAttention }) {
  const symbol = company.direction === "Improving" ? "↗" : company.direction === "Deteriorating" ? "↘" : company.direction === "Mixed" ? "↕" : "→";
  return <span className="pa-direction" data-direction={company.direction.toLowerCase()}><span aria-hidden>{symbol}</span> {company.direction} · {company.velocity}</span>;
}

function StateLabel({ state }: { state: PortfolioCompanyAttention["attentionState"] }) {
  return <span className="pa-state" data-state={state.toLowerCase().replaceAll(" ", "-")}><i aria-hidden />{state}</span>;
}

function PriorityCard({ company }: { company: PortfolioCompanyAttention }) {
  return <article className="pa-priority-card" data-rank={company.rank}>
    <header><span className="pa-rank">0{company.rank}</span><StateLabel state={company.attentionState}/></header>
    <p className="pa-sector">{company.sector} · {company.operatingModel}</p>
    <h3>{company.name}</h3>
    <Direction company={company}/>
    <p className="pa-reason"><span>{company.principalReason.kind}</span>{company.principalReason.label}</p>
    <p className="pa-summary">{company.supportingSummary}</p>
    <dl><div><dt>Potential impact</dt><dd>{company.potentialImpact}</dd></div><div><dt>Evidence confidence</dt><dd>{company.evidenceConfidence}</dd></div><div><dt>Urgency</dt><dd>{company.urgency}</dd></div></dl>
    <div className="pa-next"><span>Validate next</span><p>{company.validationQuestion}</p></div>
    {company.drillDownHref ? <Link className="pa-drill" href={company.drillDownHref} aria-label={`Open the full ${company.name} company drill-down`}>Open company intelligence <span aria-hidden>↗</span></Link> : <span className="pa-no-drill">Company drill-down · NOT BUILT</span>}
  </article>;
}

function CompanyRow({ company }: { company: PortfolioCompanyAttention }) {
  return <article className="pa-company-row">
    <span className="pa-rank">{String(company.rank).padStart(2,"0")}</span>
    <div className="pa-company-name"><strong>{company.name}</strong><small>{company.sector} · {company.operatingModel}</small></div>
    <StateLabel state={company.attentionState}/>
    <Direction company={company}/>
    <div className="pa-row-reason"><strong>{company.principalReason.label}</strong><small>{company.changedSince}</small></div>
    <div><small>Evidence</small><strong>{company.evidenceConfidence}</strong></div>
    <div><small>Impact</small><strong>{company.potentialImpact}</strong></div>
    <details><summary aria-label={`Show validation detail for ${company.name}`}>Validate <span aria-hidden>＋</span></summary><div><p><b>Question</b>{company.validationQuestion}</p><p><b>Alternative explanation</b>{company.alternativeExplanation}</p><p><b>Next action</b>{company.nextAction}</p><p><b>Missing</b>{company.missingInformation.join(" · ")}</p></div></details>
  </article>;
}

export function PortfolioAttentionQueue({ view }: { view: PortfolioAttentionView }) {
  const [state, setState] = useState("All");
  const [direction, setDirection] = useState("All");
  const [sector, setSector] = useState("All");
  const sectors = useMemo(() => ["All", ...new Set(view.companies.map(company => company.sector))], [view.companies]);
  const filtered = filterPortfolioCompanies({ state, direction, sector });
  const priorities = filtered.filter(company => company.rank <= 3);
  const remaining = filtered.filter(company => company.rank > 3);
  const reset = () => { setState("All"); setDirection("All"); setSector("All"); };

  return <div className="pa-queue">
    <section className="pa-priorities" aria-labelledby="attention-heading">
      <header><div><p className="eyebrow">Monday morning decision queue</p><h2 id="attention-heading">3 companies need attention.</h2></div><p>Ranked by the expected value of scarce operating-team attention—not by generic health or failure probability.</p></header>
      <div className="pa-priority-grid">{priorities.map(company => <PriorityCard key={company.id} company={company}/>)}</div>
    </section>
    <section className="pa-register" aria-labelledby="portfolio-register-heading">
      <header><div><p className="eyebrow">Portfolio register</p><h2 id="portfolio-register-heading">The rest of the portfolio, without manufactured drama.</h2></div><p aria-live="polite"><strong>{filtered.length}</strong> of {view.companies.length} companies shown</p></header>
      <div className="pa-filters" role="group" aria-label="Filter portfolio companies">
        <label>Attention state<select value={state} onChange={event => setState(event.target.value)}><option>All</option>{ATTENTION_STATES.map(value => <option key={value}>{value}</option>)}</select></label>
        <label>Direction<select value={direction} onChange={event => setDirection(event.target.value)}><option>All</option>{DIRECTIONS.map(value => <option key={value}>{value}</option>)}</select></label>
        <label>Sector<select value={sector} onChange={event => setSector(event.target.value)}>{sectors.map(value => <option key={value}>{value}</option>)}</select></label>
        <button type="button" onClick={reset}>Clear filters</button>
      </div>
      {filtered.length ? <div className="pa-company-list">{remaining.map(company => <CompanyRow key={company.id} company={company}/>)}</div> : <div className="pa-empty"><strong>No companies match these filters.</strong><button type="button" onClick={reset}>Show all 20 companies</button></div>}
    </section>
  </div>;
}

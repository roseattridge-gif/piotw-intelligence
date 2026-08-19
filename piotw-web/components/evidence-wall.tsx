"use client";

import { useState } from "react";
import type { Document, EvidenceObservation } from "@/types/intelligence";
import { SemanticLabel } from "./semantic-label";

export function EvidenceWall({ evidence, documents, limit }: { evidence: EvidenceObservation[]; documents: Document[]; limit?: number }) {
  const [filter, setFilter] = useState("All");
  const [selected, setSelected] = useState<EvidenceObservation | null>(null);
  const categories = ["All", ...new Set(evidence.map((item) => item.category))];
  const visible = evidence.filter((item) => filter === "All" || item.category === filter).slice(0, limit);
  const documentFor = (id: string) => documents.find((document) => document.id === id);

  return <>
    <div className="wall-toolbar"><div className="filters" aria-label="Filter evidence">{categories.map((category) => <button key={category} onClick={() => setFilter(category)} aria-pressed={filter === category}>{category}</button>)}</div><p><strong>{visible.length}</strong> of {evidence.length} observations shown</p></div>
    <div className="evidence-grid">{visible.map((item, index) => { const source = documentFor(item.documentId); return <button className="evidence-card" data-featured={index === 0 && filter === "All" ? "true" : undefined} key={item.id} onClick={() => setSelected(item)}>
      <div className="evidence-card-top"><span className="evidence-index">{String(index + 1).padStart(2, "0")}</span><span className="category">{item.category}</span><span className={`confidence confidence-${item.confidence?.toLowerCase() ?? "unknown"}`}>{item.confidence ?? "Unknown"}</span></div>
      <h3>{item.observation}</h3>
      <div className="evidence-source"><span>{source?.title ?? "Source not available"}</span><span>{source?.reportingPeriod ?? "Period not available"} · {item.page ? `p. ${item.page}` : "Page not available"}</span></div>
      <footer><SemanticLabel kind="Evidence"/><span>Inspect provenance <i aria-hidden>↗</i></span></footer>
    </button>; })}</div>
    {selected && <div className="drawer-backdrop" role="presentation" onMouseDown={() => setSelected(null)}><aside className="drawer" role="dialog" aria-modal="true" aria-labelledby="drawer-title" onMouseDown={(event) => event.stopPropagation()}>
      <button className="close" onClick={() => setSelected(null)} aria-label="Close">×</button>
      <div className="drawer-kicker"><SemanticLabel kind="Evidence"/><span>Source record</span></div><h2 id="drawer-title">Observation</h2><p className="drawer-lead">{selected.observation}</p>
      <section className="source-record"><p>This is where PIOTW got this from.</p><strong>{documentFor(selected.documentId)?.title ?? "Source not available"}</strong><span>{documentFor(selected.documentId)?.reportingPeriod ?? "Reporting period not available"}{selected.page ? ` · page ${selected.page}` : " · page not available"}</span></section>
      <h3>Source evidence</h3><blockquote>{selected.sourceExcerpt ?? "Source excerpt not available in this development fixture."}</blockquote>
      <h3>Provenance</h3><dl className="provenance"><div><dt>Document</dt><dd>{documentFor(selected.documentId)?.title ?? "Not available"}</dd></div><div><dt>Reporting period</dt><dd>{documentFor(selected.documentId)?.reportingPeriod ?? "Not available"}</dd></div><div><dt>Publication / event date</dt><dd>{selected.eventDate}</dd></div><div><dt>Page</dt><dd>{selected.page ?? "Not available"}</dd></div><div><dt>Evidence type</dt><dd>{selected.evidenceType ?? "Not available"}</dd></div><div><dt>Confidence</dt><dd>{selected.confidence ?? "Not available"}</dd></div></dl>
      <div className="drawer-interpretation"><SemanticLabel kind="Interpretation"/><h3>What PIOTW takes from it</h3><p>{selected.interpretation ?? "No item-level interpretation supplied."}</p></div>
    </aside></div>}
  </>;
}

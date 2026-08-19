"use client";
import { useState } from "react";
import type { Document, EvidenceObservation, OperationalEvent } from "@/types/intelligence";
import { SemanticLabel } from "./semantic-label";
export function Timeline({ events, evidence, documents }: { events: OperationalEvent[]; evidence: EvidenceObservation[]; documents: Document[] }) {
  const [filter,setFilter]=useState("All"); const categories=["All",...new Set(events.map(e=>e.category))];
  const sourceFor=(event:OperationalEvent)=>{const observation=evidence.find(item=>event.evidenceIds.includes(item.id));return documents.find(document=>document.id===observation?.documentId)};
  const visible=events.filter(e=>filter==="All"||e.category===filter);
  return <><div className="wall-toolbar"><div className="filters">{categories.map(c=><button key={c} onClick={()=>setFilter(c)} aria-pressed={filter===c}>{c}</button>)}</div><p><strong>{visible.length}</strong> events</p></div><ol className="timeline">{visible.map((event,index)=>{const source=sourceFor(event);return <li key={event.id}><div className="timeline-marker"><span>{String(index+1).padStart(2,"0")}</span><time>{event.date}</time></div><article><div className="timeline-meta"><span className="category">{event.category}</span><span>{event.confidence ?? "Confidence not available"}</span></div><h2>{event.title}</h2><p>{event.description}</p><footer><SemanticLabel kind="Evidence"/><span>{event.evidenceIds.length} linked observation{event.evidenceIds.length===1?"":"s"}</span><span>{source?.title??"Source not available"}</span></footer></article></li>})}</ol></>;
}

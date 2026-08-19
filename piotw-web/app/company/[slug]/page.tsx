import Link from "next/link";
import { notFound } from "next/navigation";
import { CompanyNav } from "@/components/company-nav";
import { EvidenceWall } from "@/components/evidence-wall";
import {
  DimensionScores,
  FinancialRelevance,
  InterventionPriorities,
  OperationalIndexPanel,
  PredictiveIntelligence,
  RatingDrivers,
} from "@/components/intelligence-layer";
import { SemanticLabel } from "@/components/semantic-label";
import { getCompanyBySlug } from "@/lib/data/companies";

export default async function CompanyPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const data = await getCompanyBySlug(slug);
  if (!data) notFound();
  const { company, signals, interpretations, evidence, documents } = data;

  return <>
    <CompanyNav slug={slug} active="Overview"/>

    {data.operationalIndex && data.peerBenchmark && <OperationalIndexPanel index={data.operationalIndex} benchmark={data.peerBenchmark}/>} 
    {data.ratingDrivers && <RatingDrivers drivers={data.ratingDrivers}/>} 

    <section className="brief section">
      <div className="brief-synthesis">
        <div className="brief-heading"><p className="eyebrow">Operational brief</p><span>Evidence-backed interpretation</span></div>
        <h2>Expansion is giving way to tighter operational control.</h2>
        <p className="brief-copy">{company.operationalBrief}</p>
        <div className="brief-basis"><span><strong>{evidence.length}</strong> observations</span><span><strong>{documents.length}</strong> source documents</span><span><strong>{company.evidenceCoverage.split(" · ")[0]}</strong> coverage</span></div>
        <p className="caveat">Structured interpretation of public evidence—not a statement of internal company fact.</p>
      </div>
      <div className="signals"><header className="signals-heading"><p className="eyebrow">Observed signals</p><span>Status / direction</span></header>{signals.map((signal,index)=><article key={signal.id} data-priority={["Elevated","Active"].includes(signal.status)?"high":"standard"}><span className="signal-rank">0{index+1}</span><div><header><span>{signal.category}</span><strong>{signal.status}{signal.direction?` · ${signal.direction}`:""}</strong></header><p>{signal.explanation}</p><footer><span>{signal.evidenceCount} observations</span><span>{signal.confidence??"Confidence unavailable"} confidence</span></footer></div></article>)}</div>
    </section>

    <section className="section interpretation-section"><div className="section-heading"><div><p className="eyebrow">Interpretation</p><h2>What the evidence may mean</h2></div><p>Interpretations remain visibly separate from source-grounded observations and development rating values.</p></div><div className="interpretations">{interpretations.map((interpretation,index)=><article key={interpretation.id}><span className="interpretation-index">0{index+1}</span><div><SemanticLabel kind="Interpretation"/><h3>{interpretation.title}</h3><p>{interpretation.summary}</p><footer>{interpretation.supportingEvidenceIds.length} linked observations · {interpretation.confidence??"Confidence unavailable"}</footer></div></article>)}</div></section>

    {data.dimensionScores && <DimensionScores dimensions={data.dimensionScores}/>} 
    {data.financialLinkages && <FinancialRelevance linkages={data.financialLinkages}/>} 
    {data.interventionPriorities && <InterventionPriorities priorities={data.interventionPriorities}/>} 

    <section className="story section">
      <div className="story-intro"><p className="eyebrow">Operational story</p><h2>The disclosed progression</h2><p>Read left to right: the evidence suggests a shift from selective expansion towards footprint restructuring.</p></div>
      <div className="story-flow">{company.story.map((stage,index)=><div key={stage}><span>Phase {String(index+1).padStart(2,"0")}</span><strong>{stage}</strong>{index<company.story.length-1&&<i aria-hidden>→</i>}</div>)}</div>
      <footer><span>Observed across {documents.length} disclosures</span><Link href={`/company/${slug}/timeline`}>Follow the full chronology →</Link></footer>
    </section>

    <section className="evidence-section section">
      <div className="section-heading"><div><p className="eyebrow">The evidence wall</p><h2>Show me why you think that.</h2><p>A source-led view of the observations underpinning the operational picture and its development-only intelligence layer.</p></div><Link href={`/company/${slug}/evidence`}>Open complete wall →</Link></div>
      <EvidenceWall evidence={evidence} documents={documents} limit={6}/>
    </section>

    <PredictiveIntelligence/>
  </>;
}

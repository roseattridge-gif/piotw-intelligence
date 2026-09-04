import { PortfolioAttentionQueue } from "@/components/portfolio-attention-queue";
import { getPortfolioAttentionView } from "@/lib/data/portfolio-attention";

export default function PortfolioPage() {
  const view = getPortfolioAttentionView();
  return <div className="portfolio-attention-shell">
    <header className="pa-hero">
      <div><p className="pa-demo-label">{view.label}</p><p className="eyebrow">Portfolio attention queue</p><h1>Where should<br/>we look <em>first?</em></h1></div>
      <div className="pa-hero-brief"><p>PIOTW continuously monitors the operational evidence around your portfolio and tells your operating team where attention is most likely to create or protect value.</p><dl><div><dt>Portfolio</dt><dd>20 companies</dd></div><div><dt>As of</dt><dd>{view.asOf}</dd></div><div><dt>Coverage</dt><dd>Outside-in demo evidence</dd></div></dl></div>
    </header>
    <PortfolioAttentionQueue view={view}/>
    <section className="pa-method-note"><div><p className="eyebrow">How to interpret the queue</p><h2>Attention is a decision,<br/>not a score.</h2></div><div><p>{view.orderingNote}</p><ol><li><span>01</span><strong>Prioritise</strong>Where should I look?</li><li><span>02</span><strong>Diagnose</strong>Why does it warrant attention?</li><li><span>03</span><strong>Validate</strong>What should management confirm?</li></ol></div></section>
    <section className="pa-boundary"><strong>Prototype boundary</strong><p>This simulated outside-in experience is not a complete investment re-underwrite. Internal financial performance, management plans, value-creation initiatives and investment-thesis assumptions remain unavailable unless explicitly shown.</p><div><span>Observed facts</span><span>Derived measures</span><span>Inferences</span><span>Hypotheses</span><span>Unknown / withheld</span></div></section>
  </div>;
}

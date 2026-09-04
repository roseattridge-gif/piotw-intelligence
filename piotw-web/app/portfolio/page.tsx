import { OperationalPortfolioQueue } from "@/components/operational-portfolio-queue";
import { getOperationalPortfolio } from "@/lib/data/operational-portfolio";

export default function PortfolioPage() {
  const run = getOperationalPortfolio();
  return <div className="portfolio-attention-shell"><header className="pa-hero"><div><p className="pa-demo-label">{run.mode.replaceAll("_", " ")}</p><p className="eyebrow">Portfolio attention queue</p><h1>Where should<br/>we look <em>first?</em></h1></div><div className="pa-hero-brief"><p>A working outside-in operating-review workflow built from preserved public evidence, explicit qualification policy and visible missingness.</p><dl><div><dt>Portfolio</dt><dd>{run.attention_items.length} real companies</dd></div><div><dt>Run as of</dt><dd>{run.as_of.slice(0, 10)}</dd></div><div><dt>Scientific gate</dt><dd>Not invoked</dd></div></dl></div></header><OperationalPortfolioQueue run={run}/></div>;
}

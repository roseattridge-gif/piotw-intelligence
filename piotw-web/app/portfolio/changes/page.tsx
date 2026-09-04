import Link from "next/link";
import { getOperationalPortfolio } from "@/lib/data/operational-portfolio";

export default function PortfolioChangesPage() { const run = getOperationalPortfolio(); return <main className="op-subpage"><p className="eyebrow">Since the previous run</p><h1>Portfolio changes</h1><p>Deterministic changes only. The current run is an initial baseline, so no movement is inferred.</p><Link href="/portfolio">← Attention queue</Link><div className="op-change-list">{run.changes.map((change, index) => <article key={index}><strong>{change.change_type.replaceAll("_", " ")}</strong><h2>{change.company_id?.replaceAll("-", " ") ?? "Portfolio"}</h2><p>{change.statement}</p></article>)}</div></main>; }

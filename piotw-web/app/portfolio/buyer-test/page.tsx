import Link from "next/link";
import { BuyerTestForm } from "@/components/buyer-test-form";
import { getOperationalPortfolio } from "@/lib/data/operational-portfolio";

export default function BuyerTestPage() { const run = getOperationalPortfolio(); return <main className="op-subpage"><p className="eyebrow">Buyer-comprehension mode</p><h1>Can an operating partner use this?</h1><p>Ask the participant to inspect the queue first, then answer without coaching.</p><Link href="/portfolio">← Attention queue</Link><BuyerTestForm questions={run.buyer_test.questions}/></main>; }

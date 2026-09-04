import { getOperationalPortfolio } from "@/lib/data/operational-portfolio";

export const dynamic = "force-static";

export function GET() {
  const run = getOperationalPortfolio();
  return Response.json({ status: "ok", application: "piotw-web", portfolio_run_id: run.run_id, scientific_gate_run: false });
}

import { readFileSync } from "node:fs";
import path from "node:path";
import type { OperationalPortfolioRun } from "@/types/operational-portfolio";

export function getOperationalPortfolio(): OperationalPortfolioRun {
  return JSON.parse(readFileSync(path.join(process.cwd(), "data", "portfolio-runs", "real-development-portfolio.json"), "utf8")) as OperationalPortfolioRun;
}

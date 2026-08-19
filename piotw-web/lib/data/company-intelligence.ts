import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import type { CompanyIntelligenceSnapshot } from "../../types/company-intelligence.ts";

const dataDirectory = path.join(process.cwd(), "data", "company-intelligence");

async function readSnapshot(fileName: string) {
  const raw = await readFile(path.join(dataDirectory, fileName), "utf8");
  return JSON.parse(raw) as CompanyIntelligenceSnapshot;
}

export async function getCompanyIntelligenceSnapshot(companyId: string) {
  if (!/^[a-z0-9-]+$/.test(companyId)) return null;
  try { return await readSnapshot(`${companyId}.json`); } catch { return null; }
}

export async function listCompanyIntelligenceSnapshots() {
  const files = (await readdir(dataDirectory)).filter((file) => file.endsWith(".json"));
  return Promise.all(files.map(readSnapshot));
}

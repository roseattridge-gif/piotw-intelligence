import { readFile } from "node:fs/promises";
import path from "node:path";
import type { CompanyIntelligenceV01 } from "@/types/company-intelligence-v01";

const directory = path.join(process.cwd(), "data", "company-intelligence-v01");

export async function getCompanyIntelligenceV01(companyId: string) {
  if (!/^[a-z0-9-]+$/.test(companyId)) return null;
  try {
    return JSON.parse(await readFile(path.join(directory, `${companyId}.json`), "utf8")) as CompanyIntelligenceV01;
  } catch {
    return null;
  }
}

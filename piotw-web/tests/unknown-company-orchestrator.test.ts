import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { getCompanyIntelligenceV01 } from "../lib/data/company-intelligence-v01.ts";

test("generated unknown-company object loads through the generic contract path", async()=>{
  const result=await getCompanyIntelligenceV01("cloudflare");
  assert.ok(result);
  assert.equal(result.schema_version,"piotw-company-intelligence-v0.1");
  assert.equal(result.company.display_name,"Cloudflare");
  assert.equal(result.evidence.length,2);
  assert.equal(result.conditions.length,0);
  assert.equal(result.condition_qualifications?.length,1);
  assert.equal(result.condition_qualifications?.[0].status,"INSUFFICIENT_EVIDENCE");
  assert.deepEqual(result.condition_qualifications?.[0].failed_tests,["history_depth","magnitude","persistence"]);
  assert.equal(result.capabilities.detect,"INSUFFICIENT_EVIDENCE");
  assert.equal(result.capabilities.predict,"NOT_BUILT");
  assert.equal(result.capabilities.prescribe,"WITHHELD");
  assert.equal(result.capabilities.quantify,"WITHHELD");
  assert.equal(result.predictions[0].probability,null);
  assert.equal(result.financial_impacts[0].base,null);
});

test("frontend explains withheld condition candidates without presenting them as conditions",async()=>{
  const component=await readFile(new URL("../components/company-value-intelligence.tsx",import.meta.url),"utf8");
  assert.match(component,/What we observed/);
  assert.match(component,/Why it might matter/);
  assert.match(component,/What we still do not know/);
  assert.match(component,/What would change PIOTW/);
});

test("generic loader and page contain no Cloudflare rescue path",async()=>{
  const loader=await readFile(new URL("../lib/data/company-intelligence-v01.ts",import.meta.url),"utf8");
  const page=await readFile(new URL("../app/intelligence/[companyId]/value/page.tsx",import.meta.url),"utf8");
  assert.doesNotMatch(loader,/cloudflare/i);
  assert.doesNotMatch(page,/cloudflare/i);
});

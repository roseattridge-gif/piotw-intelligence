import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { getCompanyIntelligenceV01 } from "../lib/data/company-intelligence-v01.ts";

test("canonical intelligence loader exposes one connected five-stage object", async()=>{
  const result=await getCompanyIntelligenceV01("travis-perkins");
  assert.ok(result);
  assert.equal(result.schema_version,"piotw-company-intelligence-v0.1");
  assert.equal(result.capabilities.detect,"AVAILABLE");
  assert.equal(result.capabilities.compare,"AVAILABLE");
  assert.equal(result.capabilities.predict,"NOT_BUILT");
  assert.ok(result.evidence.every(item=>item.source_hash.length===64&&item.evidence_span));
});

test("unsupported prediction and EBITDA remain explicit rather than fabricated",async()=>{
  const result=await getCompanyIntelligenceV01("travis-perkins"); assert.ok(result);
  assert.equal(result.predictions[0].probability,null);
  assert.ok(result.financial_impacts.length>0);
  assert.ok(result.financial_impacts.every(item=>item.status==="WITHHELD"));
  assert.ok(result.financial_impacts.every(item=>item.low===null&&item.base===null&&item.high===null));
});

test("value page is generic and driven through the canonical loader",async()=>{
  const source=await readFile(new URL("../app/intelligence/[companyId]/value/page.tsx",import.meta.url),"utf8");
  assert.match(source,/getCompanyIntelligenceV01\(companyId\)/);
  assert.doesNotMatch(source,/travis|perkins/i);
});

test("v0.4 second-substrate target renders without a robust percentile",async()=>{
  const result=await getCompanyIntelligenceV01("kingfisher-screwfix-ukie"); assert.ok(result);
  assert.equal(result.schema_version,"piotw-company-intelligence-v0.1");
  assert.equal(result.comparisons[0].status,"AVAILABLE");
  assert.equal(result.comparisons[0].sample_size,4);
  assert.equal(result.comparisons[0].percentile,null);
  assert.equal(result.capabilities.predict,"NOT_BUILT");
});

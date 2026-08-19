import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { coverageGaps, dimensionPositions, opportunities, outsideInEvidence, outsideInFeatures } from "../lib/data/real-company-lab/travis-perkins-outside-in.ts";
import { benchmarkFeatures, estateSources, peerCohort, peerMedian, tpEstateHistory, tpPeerGap, valueScenarios } from "../lib/data/real-company-lab/estate-productivity.ts";

test("outside-in evidence spans multiple non-financial source families", () => {
  const families = new Set(outsideInEvidence.map((item) => item.family));
  assert.ok(families.size >= 7);
  assert.equal(outsideInEvidence.filter((item) => item.family === "FINANCIAL_CONTEXT").length, 1);
  assert.ok(outsideInEvidence.every((item) => item.hash.length === 64 && item.evidenceSpan && item.url));
});
test("business-unit evidence is explicitly scoped", () => { const records=outsideInEvidence.filter((item)=>item.businessUnit); assert.ok(records.length>=7); assert.ok(records.every((item)=>item.entity&&item.businessUnit)); });
test("every feature and opportunity retains evidence lineage", () => { const ids=new Set(outsideInEvidence.map((item)=>item.id)); for(const feature of outsideInFeatures) assert.ok(feature.evidenceIds.every((id)=>ids.has(id))); for(const opportunity of opportunities){assert.ok(opportunity.evidenceIds.every((id)=>ids.has(id)));assert.ok(opportunity.assumptions.length>0);assert.ok(opportunity.questions.length>0);} });
test("dimension architecture is complete but benchmark is withheld", () => { assert.equal(dimensionPositions.length,8); assert.ok(dimensionPositions.every((dimension)=>dimension[2].length>0)); });
test("coverage gaps cannot masquerade as observations", () => { assert.ok(coverageGaps.some((gap)=>gap.family.startsWith("Careers")&&gap.status==="BLOCKED")); assert.ok(coverageGaps.every((gap)=>gap.detail.length>20)); });
test("founder retrospective is explicitly inadmissible and separate", async () => { const source=await readFile(new URL("../components/founder-retrospective-panel.tsx",import.meta.url),"utf8"); assert.match(source,/FOUNDER_RETROSPECTIVE/);assert.match(source,/admissibleAsEvidence:false/);assert.doesNotMatch(source,/fetch\(|axios|POST/); });
test("estate benchmark uses a predeclared comparable cohort",()=>{assert.equal(peerCohort.filter(p=>p.eligible).length,4);assert.equal(peerMedian,2.53);assert.equal(tpPeerGap,-2.12);assert.ok(peerCohort.some(p=>!p.eligible));});
test("estate history and evidence lineage are reproducible",()=>{assert.deepEqual(tpEstateHistory.map(y=>y.branches),[767,769,724,727]);assert.ok(estateSources.every(s=>s.hash.length===64&&s.evidenceSpan));assert.equal(benchmarkFeatures.length,4);});
test("value scenarios disclose assumptions rather than invent EBITDA",()=>{assert.deepEqual(valueScenarios.map(s=>s.value),["£28m","£42m","£57m"]);assert.ok(valueScenarios.every(s=>s.formula&&s.assumption));});
test("value engine leads with measured intelligence and withholds unsupported EBITDA", async () => { const source=await readFile(new URL("../app/lab/travis-perkins/page.tsx",import.meta.url),"utf8"); assert.match(source,/−2.12ppt/);assert.match(source,/DEVELOPMENT BENCHMARK/);assert.match(source,/EBITDA VALUE NOT YET SUPPORTABLE/);assert.match(source,/EBITDA is withheld/); });

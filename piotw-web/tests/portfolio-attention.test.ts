import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { ATTENTION_STATES, PORTFOLIO_PRIORITY_IDS, filterPortfolioCompanies, simulatedPortfolio } from "../data/portfolio-attention-demo.ts";

test("the simulated portfolio contains exactly 20 deterministically ranked companies", () => {
  assert.equal(simulatedPortfolio.companies.length, 20);
  assert.deepEqual(simulatedPortfolio.companies.map(company => company.rank), Array.from({ length: 20 }, (_, index) => index + 1));
  assert.equal(new Set(simulatedPortfolio.companies.map(company => company.id)).size, 20);
  assert.deepEqual(simulatedPortfolio.companies.slice(0, 3).map(company => company.id), [...PORTFOLIO_PRIORITY_IDS]);
});

test("the top three are differentiated and Northstar reaches the canonical drill-down", () => {
  const priorities = simulatedPortfolio.companies.slice(0, 3);
  assert.deepEqual(priorities.map(company => company.attentionState), ["Investigate now", "Watch closely", "Validate"]);
  assert.equal(new Set(priorities.map(company => company.principalReason.label)).size, 3);
  assert.equal(priorities[0].drillDownHref, "/north-star/northstar-industrial");
});

test("unknown, withheld and capability boundaries remain explicit", () => {
  assert.ok(simulatedPortfolio.companies.some(company => company.thesisRelevance === "UNKNOWN"));
  assert.ok(simulatedPortfolio.companies.some(company => company.potentialImpact === "WITHHELD"));
  for (const company of simulatedPortfolio.companies) {
    assert.ok(company.capabilities.some(capability => capability.state === "WITHHELD"));
    assert.ok(company.missingInformation.length > 0);
    assert.ok(company.validationQuestion.length > 0);
  }
});

test("improving companies are not framed as urgent problems", () => {
  const improving = simulatedPortfolio.companies.filter(company => company.direction === "Improving");
  assert.ok(improving.length >= 2);
  assert.ok(improving.every(company => company.urgency === "Routine"));
  assert.ok(improving.every(company => company.attentionState === "Pressure easing" || company.attentionState === "No immediate action"));
});

test("filters preserve the underlying states and deterministic order", () => {
  for (const state of ATTENTION_STATES) {
    const matches = filterPortfolioCompanies({ state });
    assert.ok(matches.every(company => company.attentionState === state));
    assert.deepEqual(matches.map(company => company.rank), [...matches].sort((a, b) => a.rank - b.rank).map(company => company.rank));
  }
  assert.ok(filterPortfolioCompanies({ direction: "Improving" }).every(company => company.direction === "Improving"));
  assert.ok(filterPortfolioCompanies({ sector: "Healthcare" }).every(company => company.sector === "Healthcare"));
});

test("portfolio UI uses text labels, semantic controls and accessible names", async () => {
  const source = await readFile(new URL("../components/portfolio-attention-queue.tsx", import.meta.url), "utf8");
  assert.match(source, /data-state=/);
  assert.match(source, />\{state\}<\/span>/);
  assert.match(source, /aria-label={`Open the full/);
  assert.match(source, /aria-label="Filter portfolio companies"/);
  assert.match(source, /<label>Attention state<select/);
  assert.match(source, /<details><summary aria-label=/);
});

test("portfolio copy rejects fake scoring and identifies simulated data", async () => {
  const source = await readFile(new URL("../app/portfolio/page.tsx", import.meta.url), "utf8");
  assert.match(source, /Simulated portfolio|view\.label/);
  assert.match(simulatedPortfolio.orderingNote, /not a validated score/i);
  assert.match(simulatedPortfolio.orderingNote, /Unknown is never treated as zero/i);
});

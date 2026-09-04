import assert from "node:assert/strict";
import test from "node:test";
import { getOperationalPortfolio } from "../lib/data/operational-portfolio.ts";

test("operational portfolio is real, traceable and explicitly fail-closed", () => {
  const run = getOperationalPortfolio();
  assert.equal(run.synthetic, false);
  assert.equal(run.attention_items.length, 3);
  assert.equal(run.attention_items[0].company_id, "travis-perkins");
  const failed = run.attention_items.find(item => item.company_id === "datadog");
  assert.equal(failed?.attention_state, "VALIDATE");
  assert.equal(failed?.capability_status, "INSUFFICIENT_EVIDENCE");
  assert.match(failed?.missing_information[0] ?? "", /Development-only/);
  assert.match(run.ordering_explanation, /No hidden score/);
});

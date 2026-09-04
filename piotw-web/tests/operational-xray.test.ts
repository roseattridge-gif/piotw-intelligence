import assert from "node:assert/strict";
import test from "node:test";
import { getOperationalXRay } from "../lib/data/operational-xray.ts";

test("Northstar operational X-Ray preserves evidence lineage and demo boundaries", async () => {
  const map = await getOperationalXRay("northstar-industrial");
  assert.ok(map);
  assert.equal(map.stages.length, 9);
  assert.equal(map.handoffs.length, 8);
  assert.equal(map.hotspots.length, 3);
  assert.ok(map.handoffs.every(item => item.volume?.band));
  assert.ok(map.hotspots.every(item => item.relatedIds?.includes(item.targetId)));
  assert.match(map.summary.methodologyStatus, /not validated/i);
  const sourceIds = new Set(map.sourceEvidence.map(item => item.id));
  const linkedSignals = [...map.stages, ...map.handoffs].flatMap(item => item.signals).filter(item => item.sourceEvidenceId);
  assert.ok(linkedSignals.length > 0);
  assert.ok(linkedSignals.every(item => item.classification === "Observed"));
  assert.ok(linkedSignals.every(item => sourceIds.has(item.sourceEvidenceId!)));
  assert.ok([...map.stages, ...map.handoffs].flatMap(item => item.financials).every(item => item.classification === "Modelled estimate"));
});

test("unknown companies do not receive demonstration intelligence", async () => {
  assert.equal(await getOperationalXRay("not-a-company"), null);
});

test("Travis Perkins Wall is a scoped real-company projection with visible gaps", async () => {
  const map = await getOperationalXRay("travis-perkins");
  assert.ok(map);
  assert.equal(map.dataMode, "REAL_COMPANY");
  assert.equal(map.entityScope?.primary, "Travis Perkins Merchanting");
  assert.equal(map.summary.rating, "Not scored");
  assert.match(map.summary.valueTrapped, /withheld/i);
  assert.equal(map.stages.length, 9);
  assert.equal(map.handoffs.length, 8);
  assert.ok(map.hotspots.length <= 3);
  assert.ok(map.coverageRows?.some(item => item.row === "data" && item.state === "UNAVAILABLE"));
  assert.ok(map.coverageRows?.some(item => item.row === "culture" && item.state === "WITHHELD"));
  const sourceIds = new Set(map.sourceEvidence.map(item => item.id));
  const linkedSignals = [...map.stages, ...map.handoffs].flatMap(item => item.signals).filter(item => item.sourceEvidenceId);
  assert.ok(linkedSignals.every(item => sourceIds.has(item.sourceEvidenceId!)));
  assert.ok([...map.stages, ...map.handoffs].flatMap(item => item.financials).every(item => item.classification !== "Modelled estimate"));
});

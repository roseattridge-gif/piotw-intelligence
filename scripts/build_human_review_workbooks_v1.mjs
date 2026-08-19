import fs from "node:fs/promises";
import path from "node:path";

import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve(import.meta.dirname, "..");
const pack = path.join(root, "reviewer_pack_human_ambiguity_v1");
const instructionPath = path.join(root, "docs/evidence-engine-human-review-instructions-v1.md");

const headers = [
  "case_id", "document_type", "form", "publication_date", "reporting_period",
  "bounded_evidence_context", "factual_observation", "subject", "action_or_state",
  "object", "timing", "polarity", "scope", "entity_relationship",
  "exact_evidence_span", "reviewer_confidence", "reviewer_notes",
];

const widths = [12, 18, 10, 14, 14, 90, 20, 24, 28, 24, 22, 18, 22, 22, 65, 20, 42];

function cleanInstructions(markdown) {
  return markdown.split("\n")
    .filter((line) => line.trim())
    .map((line) => [line.replace(/^#{1,6}\s+/, "").replace(/^[-*]\s+/, "• ")]);
}

async function build(reviewer) {
  const reviewerDir = path.join(pack, `reviewer_${reviewer}`);
  const cases = JSON.parse(await fs.readFile(path.join(reviewerDir, "cases.json"), "utf8"));
  const instructions = cleanInstructions(await fs.readFile(instructionPath, "utf8"));
  const workbook = Workbook.create();
  const instructionSheet = workbook.worksheets.add("Instructions");
  instructionSheet.showGridLines = false;
  instructionSheet.getRangeByIndexes(0, 0, instructions.length, 1).values = instructions;
  instructionSheet.getRange(`A1:A${instructions.length}`).format = {
    font: { name: "Aptos", size: 11, color: "#172033" },
    wrapText: true,
    verticalAlignment: "top",
  };
  instructionSheet.getRange("A1").format = {
    fill: "#17324D",
    font: { name: "Aptos Display", size: 16, bold: true, color: "#FFFFFF" },
  };
  instructionSheet.getRange(`A1:A${instructions.length}`).format.columnWidth = 115;
  instructionSheet.getRange(`A1:A${instructions.length}`).format.autofitRows();
  instructionSheet.freezePanes.freezeRows(1);

  const reviewSheet = workbook.worksheets.add("Review Cases");
  reviewSheet.showGridLines = false;
  const rows = cases.map((item) => [
    item.case_id, item.document_type, item.form, item.publication_date, item.reporting_period,
    item.bounded_evidence_context, "", "", "", "", "", "", "", "", "", "", "",
  ]);
  reviewSheet.getRangeByIndexes(0, 0, 1, headers.length).values = [headers];
  reviewSheet.getRangeByIndexes(1, 0, rows.length, headers.length).values = rows;
  reviewSheet.getRange("A1:Q1").format = {
    fill: "#17324D",
    font: { name: "Aptos", size: 10, bold: true, color: "#FFFFFF" },
    wrapText: true,
    verticalAlignment: "center",
  };
  reviewSheet.getRange("A2:Q37").format = {
    font: { name: "Aptos", size: 10, color: "#172033" },
    wrapText: true,
    verticalAlignment: "top",
    borders: { preset: "inside", style: "thin", color: "#D8E0E8" },
  };
  reviewSheet.getRange("G2:Q37").format.fill = "#FFF7D6";
  widths.forEach((width, index) => {
    reviewSheet.getRangeByIndexes(0, index, 37, 1).format.columnWidth = width;
  });
  reviewSheet.getRange("A1:Q1").format.rowHeight = 34;
  reviewSheet.getRange("A2:Q37").format.rowHeight = 92;
  reviewSheet.freezePanes.freezeRows(1);
  reviewSheet.freezePanes.freezeColumns(1);
  reviewSheet.getRange("G2:G37").dataValidation = {
    rule: { type: "list", values: ["YES", "NO", "AMBIGUOUS"] },
  };
  reviewSheet.getRange("K2:K37").dataValidation = {
    rule: { type: "list", values: ["CURRENT", "ONGOING", "PLANNED_COMMITTED", "COMPLETED_RECENT", "HISTORICAL", "HYPOTHETICAL", "UNCLEAR"] },
  };
  reviewSheet.getRange("L2:L37").dataValidation = {
    rule: { type: "list", values: ["INCREASE", "DECREASE", "POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED", "NOT_APPLICABLE", "UNCLEAR"] },
  };
  reviewSheet.getRange("N2:N37").dataValidation = {
    rule: { type: "list", values: ["ISSUER", "SUBSIDIARY", "CUSTOMER", "SUPPLIER", "COMPETITOR", "INDUSTRY", "OTHER", "UNCLEAR"] },
  };
  reviewSheet.getRange("P2:P37").dataValidation = {
    rule: { type: "list", values: ["HIGH", "MEDIUM", "LOW"] },
  };

  const inspection = await workbook.inspect({
    kind: "table",
    sheetId: "Review Cases",
    range: "A1:Q6",
    include: "values,formulas",
    tableMaxRows: 6,
    tableMaxCols: 17,
    maxChars: 5000,
  });
  console.log(inspection.ndjson);
  const errorScan = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 50 },
    summary: `Reviewer ${reviewer} formula error scan`,
  });
  console.log(errorScan.ndjson);
  for (const [sheetName, range] of [["Instructions", "A1:A18"], ["Review Cases", "A1:G8"]]) {
    const preview = await workbook.render({ sheetName, range, scale: 1, format: "png" });
    await fs.writeFile(`/tmp/piotw-human-review-${reviewer}-${sheetName.replaceAll(" ", "-")}.png`, new Uint8Array(await preview.arrayBuffer()));
  }
  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(path.join(reviewerDir, `PIOTW_Human_Review_${reviewer}_v1.xlsx`));
}

await build("A");
await build("B");

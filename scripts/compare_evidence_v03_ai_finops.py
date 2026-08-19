from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_1.guard import verify_frozen_isolation
from evidence_engine_v0_3.ai_finops import run


def render_report(results: dict) -> str:
    scope = results["scope"]
    numeric = results["numerical"]
    events = results["events"]
    n = numeric["diagnostic_counts"]
    e = events["diagnostic_counts"]
    return f"""# Evidence Engine 0.3 - AI finance/operations first-pass comparison

> **Methodological boundary:** This is an AI-assisted diagnostic comparison and does not satisfy the independent-human Evidence Engine 0.3 readiness gate. These annotations are not formal gold, are inadmissible for the Model 2 gate, and are not extraction-accuracy evidence.

## Scope

- Reviewer type: `AI_ASSISTED_FINOPS_FIRST_PASS`
- Reviewer identity: OpenAI GPT-5.6 Sol
- Status: exploratory diagnostic
- Companies: {scope['companies']} (Apple, Albemarle and Boeing)
- Documents: {scope['documents']}
- Report types: {scope['report_types']}
- AI numerical annotations: {scope['ai_numerical_annotations']}
- AI event annotations: {scope['ai_event_annotations']}

Document IDs:

{chr(10).join(f'- `{document_id}`' for document_id in scope['document_ids'])}

The pass is deliberately selective. PIOTW-only records are omission candidates, not proof that the AI reviewer failed.

## Numerical diagnostic comparison

| Classification | Count | Denominator |
|---|---:|---:|
| Exact agreement | {n['exact_agreement']} | {numeric['ai_reviewed_denominator']} AI annotations |
| Semantic agreement | {n['semantic_agreement']} | {numeric['ai_reviewed_denominator']} AI annotations |
| PIOTW missing | {n['piotw_omissions']} | {numeric['ai_reviewed_denominator']} AI annotations |
| Value disagreement | {n['value_disagreements']} | {numeric['ai_reviewed_denominator']} AI annotations |
| Accounting-basis disagreement | {n['accounting_basis_disagreements']} | {numeric['ai_reviewed_denominator']} AI annotations |
| Metric-identity disagreement | {n['metric_identity_disagreements']} | {numeric['ai_reviewed_denominator']} AI annotations |
| Period disagreement | {n['period_disagreements']} | {numeric['ai_reviewed_denominator']} AI annotations |
| Unit/scale/currency disagreement | {n['unit_scale_currency_disagreements']} | {numeric['ai_reviewed_denominator']} AI annotations |
| AI-review omission candidates | {n['ai_review_omission_candidates']} | {numeric['row_comparisons']} total comparison rows |

The 11 semantic agreements cover revenue, operating profit and operating cash flow across the reviewed Apple, Albemarle and Boeing filings. Values, signs, currencies, periods and statutory basis agree; PIOTW cites the tagged iXBRL fact while the reviewer cites the visual statement/table, so they are not called exact provenance agreements.

PIOTW did not extract nine AI-recorded metrics: two gross-margin amounts, adjusted EBITDA, net income, two total-debt values, two cash balances and unused borrowing capacity. These are parser-coverage gaps, not value mismatches.

Two value disagreements are Apple capex sign conventions. The report displays cash payments in parentheses; the reviewer records negative cash flow, while the iXBRL fact and PIOTW store positive expenditure magnitude. Both point to the same amount. This is severe until the feature definition fixes one convention, but it is a definition mismatch rather than evidence fabrication.

Two accounting-basis comparisons concern rounded narrative capex versus exact statutory cash-flow facts: Albemarle $1.3bn versus $1,261.646m and Boeing $1.6bn versus $1,582m. PIOTW's exact statutory values are the better reproducible observations; the reviewer appropriately retained the narrative definition. Both records should coexist with distinct basis/provenance.

Numerical severe disagreements: **{numeric['severe_disagreements']['count']}/{numeric['severe_disagreements']['total']} comparison rows**. Both are capex sign-convention disagreements. No wrong period, currency or 1,000x scale error was found.

## Event diagnostic comparison

| Classification | Count | Denominator |
|---|---:|---:|
| Event agreement | {e['event_agreement']} | {events['ai_reviewed_denominator']} AI annotations |
| PIOTW missed event | {e['piotw_missed_events']} | {events['ai_reviewed_denominator']} AI annotations |
| Ambiguous/source issue | {e['ambiguous']} | {events['ai_reviewed_denominator']} AI annotations |
| PIOTW false-positive candidates | {e['piotw_false_positives']} | {events['row_comparisons']} total rows |
| Duplicate PIOTW events | {e['duplicate_events']} | {events['row_comparisons']} total rows |
| AI-review omission candidates | {e['ai_review_omission_candidates']} | {events['row_comparisons']} total rows |
| Taxonomy disagreement | {e['taxonomy_disagreements']} | {events['row_comparisons']} total rows |
| Timing/context disagreement | {e['timing_context_disagreements']} | {events['row_comparisons']} total rows |

There were no same-span event agreements. PIOTW missed 14 AI-cited events, including Apple component shortages and Greater China demand weakness; Albemarle investment/capacity expansion; Boeing recovery, pricing pressure, backlog decline, production disruption, labour stoppage, announced workforce reduction, cost reduction and liquidity concern.

PIOTW produced 63 events not selected by the AI pass. Forty are plausible AI-review omission candidates requiring human adjudication. The remaining records are 21 likely keyword false positives and two near-duplicates: hypothetical risks, biographies containing “restructuring,” business-continuity “redundancy,” mineral-resource “simplification,” and generic accounting disclosures. Severe event comparisons either miss major current Boeing interventions/constraints or could encode semantically false/duplicated restructuring or redundancy events.

## Severe disagreement detail

Numerical:

- `num-005`: Apple FY2023 capex, reviewer cash-flow sign negative versus PIOTW expenditure magnitude positive.
- `num-010`: Apple 2024 nine-month capex, the same sign-convention mismatch.

Events:

- `event-011`: PIOTW missed Boeing's current production/delivery disruption.
- `event-013`: PIOTW missed Boeing's announced roughly 10% workforce reduction.
- `event-014`: PIOTW missed Boeing's current discretionary-spend/capex reduction.
- `event-015`: PIOTW missed Boeing's ratings/liquidity concern.
- `event-017`: PIOTW interpreted business-continuity “redundancy” as a workforce event.
- `event-022`: PIOTW treated a hypothetical works-council restructuring risk as a current event.
- `event-028` and `event-029`: PIOTW extracted executive biographies as current restructuring events.
- `event-033` and its near-duplicate: PIOTW extracted generic non-GAAP restructuring-charge definitions as company events.
- `event-076`: PIOTW extracted a hypothetical Boeing restructuring clause as a current event.

This is the highest-priority extraction issue: sentence-level keyword patterns do not adequately distinguish an actual company event from hypothetical, biographical, accounting or unrelated uses of the same word.

## Source-pack issue: Albemarle 2024

`ee03-alb-0000915913-24-000156` is a confirmed source-pack completeness defect.

- The SEC primary HTML contains a link to `a3q24earningsreleaseex991.htm`.
- The local source collection does not contain that exhibit.
- The four-page reviewer PDF contains only the Form 8-K wrapper. It states that the results and non-GAAP reconciliations are in Exhibit 99.1 but does not include the exhibit body.
- PIOTW extracted zero financial facts from the wrapper, so there is no current unfair numerical advantage.
- Comparing absent-exhibit results would nevertheless be methodologically unfair.

The blinded human-review pack needs a versioned repair before formal review: preserve the current pack, create a corrected version containing the actual exhibit, and audit all results-wrapper documents for linked-but-absent exhibits.

## Reviewer workflow usefulness

The instructions were sufficient for source-grounded values, periods, currency, scale, evidence spans and ambiguity. Revenue, statutory operating profit and operating cash flow were consistently interpretable. More finance judgment was required for adjusted EBITDA, rounded versus exact capex, gross-margin amount versus percentage, restricted cash and company-defined liquidity measures.

Before human review, the rubric should add:

- canonical case-sensitive metric and event names;
- an explicit capex sign convention;
- separate fields for reported raw value and normalized value;
- a rule preferring exact primary-statement figures while retaining rounded narrative alternatives;
- explicit distinctions between gross-margin amount and gross-margin percentage;
- event timing/status fields for actual, planned, hypothetical, historical and completed;
- a source-completeness check for linked exhibits before a document is assigned.

No review-time saving can be inferred because this was not a timed human study.

## Recommended actions

### Fix before human review

- Repair linked-exhibit completeness and audit all wrapper filings.
- Freeze the reviewer vocabulary and capex sign convention.
- Prevent generic keyword hits from being treated as factual company events.

### Improve reviewer instructions

- Add canonical metric/event dictionaries and timing/status examples.
- Separate raw reported values from normalized values.

### Extraction improvements

- Add gross margin, adjusted EBITDA, debt, cash and liquidity coverage with basis-aware definitions.
- Add negation, hypothetical/risk, biography, accounting-note and historical-context suppression.
- Retain visual-table page provenance alongside iXBRL provenance.

### No action / reviewer difference

- Retain both exact statutory capex and rounded narrative capex when clearly labelled.
- Treat the 40 PIOTW-only plausible events as adjudication candidates, not confirmed reviewer errors.

## Official status

**NOT READY**

The frozen Evidence Engine 0.3 readiness decision is unchanged. No outcome data was accessed, no Model 2 was trained, and this diagnostic is not admissible for the human-readiness gate.
"""


def main() -> None:
    before = verify_frozen_isolation(ROOT)
    results = run(ROOT)
    (ROOT / "docs/evidence-engine-v0.3-ai-finops-first-pass-comparison.md").write_text(
        render_report(results)
    )
    after = verify_frozen_isolation(ROOT)
    if before != after or len(after) != 12:
        raise RuntimeError("protected artifact integrity changed")
    print(json.dumps({"status": results["official_readiness_status"], "scope": results["scope"],
                      "numerical": results["numerical"], "events": results["events"],
                      "protected_artifacts": len(after)}, indent=2))


if __name__ == "__main__":
    main()

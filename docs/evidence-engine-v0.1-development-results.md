# Evidence Engine 0.1 — development results

## Honest status

The smallest safe corpus is implemented as 10 synthetic companies with two annual-report-style periods each (20 reports). This choice avoids all validation/holdout evidence and outcomes while partition boundaries for real development documents are formalized.

Synthetic gold accuracy tests deterministic plumbing. It does **not** establish accuracy on real issuer PDFs.

## Measured run

Command: `make evidence-demo`

| Measure | Result |
|---|---:|
| Companies | 10 synthetic |
| Reports | 20 |
| Gold numeric facts | 140 |
| Numerical extraction accuracy | 100% |
| Gold event labels | 40 |
| Event classification recall | 100% |
| Reviewer correction rate | 0% |
| Missing-value rate | 0% |
| Duplicate-event rate | 0% |
| Provenance completeness | 100% |
| Facts with retained exact spans | 100% |
| LLM calls/cost | 0 / $0 |
| Direct collector cost | $0 |
| Measured local runtime | approximately 0.38 seconds total / 0.019 seconds per synthetic report |
| Rebuildable SQLite size | approximately 496 KB / 25 KB per synthetic report |

The generated result is `data/derived/evidence_engine_v0_1/demo_output.json`.

## Objectively extractable observations now

The deterministic parser supports labelled values for revenue, EBITDA, operating profit, operating margin, gross margin, operating cash flow, free cash flow, cash conversion, net debt/net cash, leverage, working capital, inventory, receivables, liquidity, capex, investment commitments, restructuring provisions/charges, exceptional costs, impairment charges, redundancy costs, and site-closure costs.

Supported value forms include GBP/USD/EUR with thousand/million/billion scales, percentages, and `x` ratios. Unsupported or absent values remain missing.

Language observations cover all atomic categories in the 0.1 taxonomy. Each is a matched occurrence, not a vague pressure score.

## Longitudinal features available

- revenue year-on-year change %
- operating-margin change in basis points
- free-cash-flow change %
- net-debt change %
- cash-conversion change in basis points
- capex growth %
- restructuring-charge change %
- impairment change %
- exceptional-cost change %
- per-event current count
- mention-count change
- new-appearance flag
- persistence periods

The Example fixture produces, among other facts, operating margin change −110bps, revenue change −2%, net debt change +11%, capex growth +23.08%, and a new cost-reduction event. Every report-derived feature contains evidence IDs.

## Jobs features available

- open vacancy count and count change
- new-vacancy velocity and closed vacancies
- counts, changes, and shares for operations, procurement, transformation, finance, AI/data, and manufacturing
- geographic hiring expansion
- senior hiring change

The Example fixture moves from six to four open jobs, operations hiring falls by three roles, transformation hiring appears, and two AI/data roles are present. These are observations only; the engine assigns no pressure interpretation.

## Cost and scale

Current code uses local deterministic parsing and public/fixture collectors, so direct API and LLM cost is $0. Real operational cost will primarily be source retrieval, storage, and human review.

| Scale | Reports at two periods/company | Deterministic compute/API cost | Synthetic-like structured DB estimate | Human factual review at an illustrative 1–3 min/report |
|---:|---:|---:|---:|---:|
| 100 companies | 200 | $0 direct API/LLM | ~5 MB plus raw documents | ~3.3–10 hours |
| 1,000 companies | 2,000 | $0 direct API/LLM | ~50 MB plus raw documents | ~33–100 hours |
| 10,000 companies | 20,000 | $0 direct API/LLM | ~500 MB plus raw documents | ~333–1,000 hours |

Those DB figures extrapolate synthetic records and exclude raw PDFs. Real PDFs commonly dominate storage and could add hundreds of megabytes at 100 companies, gigabytes at 1,000, and tens or hundreds of gigabytes at 10,000 depending on report size and retention. Jobs snapshot costs are currently $0 for documented public routes, but collection time/storage have not been benchmarked at scale.

## Remaining subjective elements

- deciding whether two accounting metrics are genuinely comparable;
- choosing the correct group/segment and adjusted/statutory measure;
- correcting ambiguous extraction;
- classifying context-sensitive language and novelty;
- determining objective severity when text is qualitative;
- resolving job function/seniority where titles are ambiguous.

These judgments validate facts; none creates a 0–1 predictor score.

## Known technical weaknesses

The biggest weakness is that the report pipeline has only been quality-measured on clean synthetic labelled text. It has not yet demonstrated table extraction, layout recovery, footnote association, or comparable-metric resolution across heterogeneous real annual/interim reports.

Additional difficulties remain:

- adjusted versus statutory metrics;
- changing segments, definitions, currencies, and restatements;
- acquisitions/disposals breaking comparability;
- missing comparative values;
- duplicated references and boilerplate risk language;
- careers sites without historical snapshots;
- reposted jobs or changed posting IDs;
- incomplete careers feeds and ambiguous function mapping.

## Readiness for a genuine Model 2

**Not yet ready.** The architecture, provenance, cutoff enforcement, review mechanics, feature calculations, and frozen isolation are ready for a real development-corpus extraction trial. A genuine Model 2 should wait until a legally safe real-report corpus achieves measured accuracy and acceptable correction/missing/duplicate rates. No predictive model was trained in this phase.

The strategic answer today is therefore: **PIOTW can turn controlled messy-looking evidence into traceable longitudinal facts without subjective predictive scoring, but it has not yet proved that capability on heterogeneous real company reporting.**

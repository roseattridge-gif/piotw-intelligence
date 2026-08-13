# Three-company retrospective pilot report

## Decision

**Do not expand or describe v0.1 as proprietary intelligence. Gate 4 — incremental alpha — is not passed.**

The project demonstrated that dated public disclosures can be retained, hashed, parsed into fact-level evidence, separated from later outcome evidence and scored reproducibly for £0 external spend. It did not demonstrate predictive superiority. The PIOTW operational model's Brier score was 0.286; the simple inventory/revenue-divergence comparator scored 0.268 in this three-company sample. Lower is better.

## Design

- Prediction cutoff: 31 December 2021.
- Outcome horizon: 30 June 2023.
- Candidate frame: 30 UK-listed industrial names documented before outcome inspection.
- Pilot: Chemring, Vesuvius and Bodycote, selected reproducibly by the lowest SHA-256 key within three sector strata.
- Prediction evidence: one official, dated, pre-cutoff disclosure per company.
- Outcome evidence: separately retained official post-cutoff disclosures.
- Validation: 24 fact observations, eight per company, manually checked against retained document pages.
- Model: deterministic weighted evidence; no LLM and no API expenditure.

This is a retrospective exploratory pilot, not a blind backtest. Although the protocol and selection were frozen before outcome research, the implementation and evidence interpretation were completed by the same researcher who subsequently inspected the outcomes. The sample is not statistically powered.

## Results

| Company | PIOTW probability | Confidence | Primary label | Result |
|---|---:|---:|---:|---|
| Chemring | 14.8% | 62.6% | 1 | False negative |
| Vesuvius | 74.7% | 61.8% | 1 | True positive |
| Bodycote | 26.1% | 61.0% | 0 | True negative in reviewed outcome material |

At a 0.5 threshold, precision was 1.00 and recall 0.50. With n=3 these figures are descriptive only.

| Model | Brier score |
|---|---:|
| Inventory/revenue divergence | **0.268** |
| PIOTW operational | 0.286 |
| Financial stress count | 0.347 |
| Margin deterioration | 0.440 |
| Leave-one-company-out base rate | 0.500 |

## Evidence interpretation

### Chemring

The eligible FY2021 disclosure reported labour and supply-chain pressure and an 84%-covered order book, but also improved operating margins, 105% cash conversion, lower inventory and sharply reduced net debt. The model therefore assigned low intervention probability. Within the horizon, Chemring announced a £90m capacity expansion programme. This is a genuine false negative under the frozen label and shows that strong financial execution can coexist with a major capacity response.

### Vesuvius

The eligible H1 2021 disclosure quantified £10.3m of excess freight cost, a working-capital-related fall in cash conversion, an intended inventory build and a £28m capacity programme. It also showed improving margin and working-capital ratios. The model ranked Vesuvius highest. Its FY2022 results later documented £89m of capex, named capacity expansions and inventory reduction. The direction was useful, but much of the later outcome was already foreshadowed explicitly; this is detection of disclosed intent, not discovery of a hidden condition.

### Bodycote

The November 2021 update reported an automotive revenue shortfall caused by sector supply bottlenecks and lowered full-year revenue expectations. It simultaneously reported healthy margins, strong cash flow and successful pass-through of energy and labour inflation. The reviewed FY2022 disclosure showed only a 30bp margin decline and no separately quantified project meeting the preregistered major-capacity threshold. The negative label is limited to the reviewed primary material and is not proof that no other qualifying announcement existed.

## Stage gates

| Gate | Decision | Evidence |
|---|---|---|
| 1 Extraction | **Provisional pass for feasibility** | 24/24 retained observations manually traced to a page/location; sample too small for accuracy claims |
| 2 Inference | **Provisional pass for explainability** | All probabilities reconstruct from stored bounded contributions; no inter-rater consistency test |
| 3 Predictive signal | **Not established** | One true positive, one false negative, one true negative; n=3 |
| 4 Incremental alpha | **Fail** | PIOTW Brier 0.286 versus best simple baseline 0.268 |
| 5 Trust | **Not tested externally** | Evidence ledger exists; no expert-user study |
| 6 Willingness to pay | **Not tested** | No buyer test authorised or undertaken |

## What was learned

1. Availability-date lineage and exact audit trails are technically feasible without paid infrastructure.
2. Explicit narrative/operational evidence adds useful context, but v0.1 did not outperform a simple comparator.
3. The primary composite label is too broad: a capacity investment can reflect strong demand, not operational deterioration.
4. Vesuvius demonstrates a leakage-adjacent conceptual problem: when management explicitly announces a capacity programme before cutoff, predicting a later programme is persistence, not hidden-signal inference.
5. A larger test should separate **announced-plan continuation** from **previously unannounced intervention**, and should use at least two prediction dates per company.

## Recommended next decision

Do not automatically scale collection to 30 companies. If the hypothesis is to receive one further low-cost test, first revise the label ontology, exclude already-announced outcomes, add independent outcome adjudication, and run a genuinely blinded 10-company validation slice. That is a new stage-gate decision, not unfinished implementation of this pilot.

## Primary sources

- Chemring FY2021 results, 14 December 2021: https://www.chemring.com/~/media/Files/C/Chemring-V3/press-releases/fy-results-pr-14-12-2021.pdf
- Chemring interim results, 6 June 2023: https://www.chemring.com/media/press-releases/2023/06-06-2023
- Vesuvius H1 2021 results, 29 July 2021: https://www.vesuvius.com/content/dam/vesuvius/corporate/investors/results-reports-and-presentations/results/2021/Vesuvius%20plc%20-%20H1%202021%20Results%20RNS%20FINAL_.pdf
- Vesuvius FY2022 results, 2 March 2023: https://www.vesuvius.com/en/media/press-releases/corporate/2023/2022-full-year-results.html
- Bodycote trading update, 23 November 2021: https://www.bodycote.com/wp-content/uploads/2021/11/211123-Bodycote-November-Trading-Update-2021-FINAL.pdf
- Bodycote FY2022 results, 17 March 2023: https://www.bodycote.com/wp-content/uploads/2023/03/Bodycote-full-year-results-2022.pdf

# PIOTW Rules 1.0.0 — complete signal inventory

## Audit boundary

This document describes the code frozen at commit `eac7499a8ea659e126036675f773471a3d3451f6` (short form `eac7499`). The frozen model specification hash is `213d13648f4f`. It does not use or inspect post-cutoff outcomes.

The authoritative files are:

- `config/models/restructuring_rules_1_0_0.json`
- `validation/restructuring_v2.py`, function `predict_restructuring`
- `data/restructuring_v2/features.csv`
- `data/restructuring_v2/evidence.csv`

## What the model predicts

For a listed parent company at a specified cutoff date, PIOTW Rules 1.0.0 estimates the probability that the company will make the **first public announcement of a previously unannounced material restructuring** during the next 365 days.

The outcome window is exactly `(cutoff, cutoff + 365 days]`: the cutoff itself is excluded and the last day is included. A programme already announced on or before the cutoff is not an eligible future outcome.

## Complete formula

Let:

- `P` = pressure language score
- `M` = margin pressure score
- `C` = cash pressure score
- `K` = contrary strength score

Each value must be between 0 and 1 in increments of 0.05. Missing or extra features are an error.

The starting log-odds are:

`ln(0.12 / 0.88) = -1.99243016469`

The complete raw score is:

`S = -1.99243016469 + 1.4P + 0.9M + 0.7C - 0.8K`

The probability is:

`probability = 1 / (1 + exp(-S))`

The stored probability is rounded to six decimal places. Feature contributions are stored without rounding. There are no additional caps, floors, interactions, trees, fitted coefficients, or hidden features. The sigmoid naturally keeps the answer between 0 and 1.

This is a hand-specified rules model. It is not a fitted statistical or machine-learning model. No LLM call occurs in prediction calculation. The four inputs are manually judged and recorded before the deterministic calculation, with the reviewer identified in the data as `codex-primary-1`; the repository does not provide a programmatic provenance breakdown between human drafting and any AI assistance used during that research work.

## Every model signal

| Signal | Plain-English meaning | Source | Raw evidence extracted | Transformation | Direction | Weight/contribution | Why it was included |
|---|---|---|---|---|---|---|---|
| `pressure_language` | Measures whether management describes unusually strong or repeated operational pressure, self-help, cost control, footprint change, simplification, or intervention before the cutoff. | A human review of the selected latest eligible issuer disclosure set; in the frozen data this is normally an annual report and occasionally a results announcement or prospectus. | A page-referenced narrative observation covering pressure statements and contradictory evidence. Keyword excerpts could help the reviewer find passages, but did not set the score. | Human assigns 0.00–1.00 in 0.05 steps using the rubric below; model multiplies it by 1.4. | Higher increases predicted restructuring probability. | `+1.4 × score`; maximum +1.4. A 0.05 step changes the raw score by +0.07. | Broad operational pressure was the central business hypothesis carried forward from the pilot. Exact thresholds and weight have **no documented empirical derivation**. Classification: theoretically motivated/prior business reasoning for the concept; heuristic assumption for the scale and weight. |
| `margin_pressure` | Measures deterioration in margins or major quantified profitability headwinds before the cutoff. | The same manually reviewed disclosure set. | Page-referenced margin figures, movements, loss-making units, expectations, and relevant offsets summarized in the observation. | Human assigns 0.00–1.00 in 0.05 steps; model multiplies it by 0.9. | Higher increases probability. | `+0.9 × score`; maximum +0.9. A 0.05 step changes raw score by +0.045. | Margin deterioration was treated as a plausible precursor to management intervention and appeared in earlier financial-stress reasoning. Exact band boundaries and weight have **no documented empirical derivation**. Classification: theoretically motivated/prior business reasoning; heuristic exact implementation. |
| `cash_pressure` | Measures weakening cash generation, working-capital absorption, leverage, liquidity, covenant, or refinancing pressure. | The same manually reviewed disclosure set. | Page-referenced free cash flow, cash conversion, working capital, debt/liquidity and related statements summarized in the observation. | Human assigns 0.00–1.00 in 0.05 steps; model multiplies it by 0.7. | Higher increases probability. | `+0.7 × score`; maximum +0.7. A 0.05 step changes raw score by +0.035. | Cash constraint was treated as another plausible trigger for intervention and was present in earlier financial-stress reasoning. Exact bands and weight have **no documented empirical derivation**. Classification: theoretically motivated/prior business reasoning; heuristic exact implementation. |
| `contrary_strength` | Measures evidence arguing against near-term restructuring: strong growth, orders, margin/cash resilience, liquidity, recovery, or an intervention already completed. | The same manually reviewed disclosure set. | Page-referenced positive and offsetting evidence summarized in the observation. | Human assigns 0.00–1.00 in 0.05 steps; model multiplies it by −0.8. | Higher reduces probability. | `−0.8 × score`; maximum reduction −0.8. A 0.05 step changes raw score by −0.04. | The protocol required both supporting and contradictory evidence rather than only risk evidence. The exact composite, bands, and weight have **no documented empirical derivation**. Classification: prior business reasoning and a safeguard against one-sided review; heuristic exact implementation. |

There are **four actual model features**, not 54 and not a Pressure/Expansion feature set.

## Actual scoring rubrics

The common instruction is to score the latest eligible disclosure set as a whole, use the lower anchor when evidence falls between anchors, and record support and contradiction.

| Feature | Score range | Frozen instruction |
|---|---:|---|
| Pressure language | 0.00–0.15 | No pressure language or only routine risk boilerplate. |
|  | 0.20–0.35 | Specific but contained inflation, supply, labour, delivery, utilisation, or efficiency pressure. |
|  | 0.40–0.55 | Repeated or quantified operational pressure, explicit self-help, or cost-control language. |
|  | 0.60–0.75 | Multiple persistent pressures or explicit cost, footprint, simplification, or restructuring activity that is not itself an eligible future outcome. |
|  | 0.80–1.00 | Severe, pervasive, and quantified intervention pressure. |
| Margin pressure | 0.00–0.15 | Margin improving materially with no credible deterioration. |
|  | 0.20–0.35 | Stable/slightly weaker margin or unquantified headwind. |
|  | 0.40–0.55 | Clear deterioration below 100 basis points or substantial offsetting pressure. |
|  | 0.60–0.75 | Deterioration around 100–200 basis points or major quantified headwinds. |
|  | 0.80–1.00 | Deterioration above 200 basis points, a loss-making unit, or a withdrawn margin expectation. |
| Cash pressure | 0.00–0.15 | Strong positive cash generation/conversion and improving liquidity. |
|  | 0.20–0.35 | Positive but weaker cash or contained working-capital absorption. |
|  | 0.40–0.55 | Material cash-conversion decline, leverage increase, or inventory/receivables absorption. |
|  | 0.60–0.75 | Weak/negative free cash flow or substantial working-capital divergence. |
|  | 0.80–1.00 | Acute liquidity, covenant, refinancing, or sustained negative-cash pressure. |
| Contrary strength | 0.00–0.15 | No material contrary evidence. |
|  | 0.20–0.35 | Limited offset such as orders, pricing, or liquidity. |
|  | 0.40–0.55 | Credible mixed evidence or recovery indicators. |
|  | 0.60–0.75 | Strong growth, order visibility, margin/cash resilience, or completed intervention. |
|  | 0.80–1.00 | Multiple strong quantified contrary indicators with no unresolved pressure. |

There is no special numeric rule for the gaps between printed bands. The common rule says to choose the lower anchor when evidence falls between anchors. The exact interpretation remains a reviewer judgment.

## What enters and does not enter

The prediction function receives only the four numbers above. It does not receive document text, issuer identity, industry, market data, dates, outcomes, job data, news, or a prompt. Evidence IDs and hashes are recorded with the immutable prediction but do not change the probability. Confidence is separate and does not change probability.

The v2 registry assigns confidence `0.48` when an evidence ID exists and `0.0` otherwise. All 289 frozen predictions have evidence IDs and therefore all have confidence `0.48`. The more nuanced wording in the model configuration about lowering confidence for partial coverage is not implemented as a graduated calculation.

## Origin and rationale audit

The rule first appears in the earlier frozen v1 registration work identified by `origin_git_commit` `a4ca5b8…`; v2 made it machine-readable and carried it forward unchanged before v2 outcomes. The validation plan says the inputs are manually assessed ordinal evidence and calls out the 12% prior and fixed weights. The code and history do not document a statistical fit or optimization for the main model.

| Element | Origin classification | Finding |
|---|---|---|
| Operational pressure concept | Theoretically motivated / prior business reasoning | Fits the hypothesis that persistent operational pressure can precede intervention. |
| Margin pressure concept | Theoretically motivated / prior business reasoning | A financial-stress indicator carried from earlier reasoning. |
| Cash pressure concept | Theoretically motivated / prior business reasoning | A financial constraint indicator carried from earlier reasoning. |
| Contrary evidence | Prior business reasoning | Intended to make the assessment two-sided. |
| Exact feature weights | Heuristic assumption | **No documented rationale found** for 1.4, 0.9, 0.7, or −0.8 individually. |
| Exact score bands and 0.05 grid | Heuristic assumption / implementation convenience | **No documented rationale found** for the exact cut points or step size. |
| 12% prior | Prior business assumption | It is frozen in target/model configuration. **No documented empirical derivation found.** |
| Logistic probability mapping | Implementation convenience | Provides a bounded monotonic probability around a prior; it was not calibrated or fitted for Rules 1.0.0. |
| Confidence 0.48 | Heuristic assumption | Described as the v1 value for one manually checked primary disclosure. **No documented empirical derivation found.** |

## Frozen comparator models

Comparators are evaluation references, not additional inputs to Rules 1.0.0.

| Comparator | Inputs and formula | Thresholds / mapping | Rationale and caveat |
|---|---|---|---|
| Constant prior | No inputs; always returns 0.12. | None. | Tests whether the rule improves on its own background rate. The 12% derivation is not documented. |
| Leave-one-company-out development rate | Mean binary outcome across scored v1 development occasions after excluding every row for the prediction company. Unseen companies use all scored development occasions; uncertain labels are omitted. | Direct empirical rate; error if no rows remain. | A simple empirical base-rate comparator that avoids using the same company’s development outcomes. It does not use v2 outcomes. |
| Financial-stress rule | `margin_flag = 1` if margin pressure ≥0.60; `cash_flag = 1` if cash pressure ≥0.60; probability `(margin_flag + cash_flag + 1)/5`. | Neither flag = 0.20; one = 0.40; both = 0.60. | Inherited from the pre-v1 pilot. The mapping is heuristic rather than calibrated. |
| Disclosure-language rule | Unicode-normalizes and lowercases eligible text; searches a frozen term list. A hit triggers unless within 120 characters of “historical”, “completed”, “previously announced”, or “already announced”. | Hit = 0.20; no hit = 0.12. | A simple language comparator. In the v2 evaluation path, `eligible_text` is the manually written evidence observation, not the full source document, so this comparator is partly mediated by the reviewer’s summary. |
| Financial-only logistic | Standardizes margin and cash using frozen v1 means/SDs, then computes `sigmoid(−1.6559048297 + 0.2809763078 × z_margin + 0.8546439433 × z_cash)`. | No hard input thresholds. | This comparator **is** a statistical model fitted by deterministic gradient descent to the 20-row v1 development set, with L2-penalized slopes. It is not PIOTW Rules 1.0.0 and is forbidden from refitting for v2. |

The evaluation configuration also uses a 0.5 classification threshold, but that threshold does not alter the probabilities.

## Methodological observations specific to the signals

- `pressure_language` can overlap with margin and cash evidence, so the same adverse disclosure may raise multiple inputs.
- `contrary_strength` often uses the inverse of the same margin/cash evidence and also includes growth, orders, liquidity, and completed intervention. It is a broad composite rather than a cleanly independent signal.
- Explicit pre-cutoff restructuring activity can raise `pressure_language`, although the same already-announced programme is excluded from the future target. This is target-adjacent and relies on careful manual separation of an old programme from a genuinely new one.
- The strongest possible positive inputs still produce a bounded rule result because of the negative starting log-odds; these are designed scores, not empirically calibrated probabilities.
- All four inputs are subjective manual judgments by one recorded reviewer. There is no independent duplicate scoring or inter-rater reliability record.


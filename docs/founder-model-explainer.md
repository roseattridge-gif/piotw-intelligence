# Founder model explainer

## What Rose has actually built so far

PIOTW currently has a real, reproducible historical prediction experiment for one narrow question:

> Based on a selected company disclosure available by a cutoff date, how likely is that company to announce a previously unannounced material restructuring during the next 365 days?

It is not yet the full Pressure/Expansion intelligence system. It is a manually researched, rules-based restructuring experiment with automated document handling, arithmetic, checks, and immutable recording.

### 1. What does the prototype currently do?

For each eligible company-date occasion, a reviewer reads a selected pre-cutoff disclosure, records evidence, assigns four scores, and the software converts those four scores into a restructuring probability. The software then stores the probability with evidence references and hashes so it cannot quietly be changed later.

The frozen v2 set contains 289 such predictions. Two of the original 291 occasions—Dowlais at the 2020 and 2022 cutoffs—were excluded by the frozen `uninterpretable_entity_at_cutoff` rule because Dowlais was incorporated and listed only after those cutoffs.

### 2. What information does it look at?

For this frozen experiment, it overwhelmingly looks at one annual report per occasion. Of the 289 evidence records, 285 are annual reports/accounts, three are final or full-year results releases, and one is a prospectus.

The reviewer looks for operational pressure, margin deterioration, cash pressure, and strong facts pointing the other way. The software does not independently read dozens of external feeds to make this prediction.

### 3. What patterns is it looking for?

It asks four questions:

1. Is management describing sustained or severe operational pressure and intervention?
2. Are margins deteriorating?
3. Is cash, working capital, debt, or liquidity under pressure?
4. Is there strong contrary evidence, such as growth, orders, improving margins, strong cash, liquidity, or a completed intervention?

The first three push risk upward. The fourth pushes it downward.

### 4. Why might those patterns precede restructuring?

The business theory is understandable: persistent operating problems, falling profitability, or cash constraints can force management to reduce costs, close sites, simplify operations, or reorganize. Strong demand, improving economics, and financial resilience can make that less likely.

That is a plausible theory, not proof that the selected weights produce accurate probabilities. The repository does not document empirical derivation for the exact weights, thresholds, or 12% starting probability.

### 5. How does it turn them into a probability?

It starts from a 12% prior probability. It converts that prior into a raw log-odds score, adds:

- 1.4 times the operational-pressure score;
- 0.9 times the margin-pressure score;
- 0.7 times the cash-pressure score; and
- minus 0.8 times the contrary-evidence score.

It then applies a standard S-shaped mathematical conversion called a sigmoid, which turns any raw score into a number between 0% and 100%. This conversion was specified by hand; it is not a fitted machine-learning model.

### 6. What part is manual?

The intellectually decisive part is manual. A reviewer selected or substituted the evidence source, read it, wrote the page-referenced observation, separated already-announced activity from a possible future event, and assigned every one of the four feature values.

Across the frozen predictions that is 1,156 manually assigned feature values: 289 predictions × four scores. There is no automatic financial-statement parser that generates these scores, and no independent second reviewer in the frozen records.

### 7. What part is automated?

Code automatically built and hashed the cohort, downloaded and checked many PDFs, extracted PDF text, generated keyword-led review excerpts, validated dates and score formats, joined the evidence to each occasion, calculated the probability, produced contribution traces, hashed the evidence snapshots, and wrote immutable SQLite/JSON prediction records.

So it is best described as **a manually coded research process with automated collection assistance, quality checks, mathematical scoring, and freezing**. It is neither a fully automated prediction engine nor a spreadsheet-only exercise.

### 8. What has been validated so far?

The earlier v1 experiment tested the same rules on a small 20-occasion development set and implemented comparison metrics and baselines. Repository documentation records some promising ranking behaviour, but also a formal gate that remained indeterminate and a failure to identify positives at a 0.5 classification threshold.

The v2 infrastructure has been tested for reproducibility, no-outcome execution, hashes, and immutability. The 289 v2 predictions were frozen before outcomes.

### 9. What has not been validated?

The 289 v2 predictions have not been outcome-adjudicated or evaluated. This audit deliberately did not inspect any post-cutoff outcome. Therefore the broad-sample discrimination, calibration, event yield, sector robustness, and commercial usefulness of Rules 1.0.0 remain unvalidated.

The exact 12% prior, four weights, manual scoring consistency, and probability calibration have not been established empirically in the frozen model.

### 10. How far are we from the broader PIOTW vision?

The repository contains useful scaffolding and specifications for a much broader evidence system, but the frozen v2 model does not yet combine jobs, contracts, filings, news, planning, web activity, peer comparisons, sector indexes, Pressure, and Expansion into a live intelligence product.

The important achievement is narrower: Rose has built a traceable end-to-end prediction laboratory that forces a cutoff, preserves evidence references, freezes inputs and predictions, and can later be judged honestly. The next question—deliberately paused—is whether its predictions work.

## One-page signal map

| Source | Evidence recorded | Human signal judgment | Numeric feature | Model contribution | Output |
|---|---|---|---|---|---|
| Usually one annual report; occasionally results or a prospectus | Source title/URL/date/basis, page references, narrative observation, already-announced exclusion | Severity of operating pressure | `pressure_language` 0–1 | score × +1.4 | Part of 365-day restructuring probability |
| Same disclosure | Margin figures, movements, headwinds, loss-making units, offsets | Severity of margin pressure | `margin_pressure` 0–1 | score × +0.9 | Part of probability |
| Same disclosure | Cash conversion, free cash flow, working capital, debt/liquidity | Severity of cash pressure | `cash_pressure` 0–1 | score × +0.7 | Part of probability |
| Same disclosure | Growth, orders, margin/cash resilience, liquidity, recovery, completed intervention | Strength of evidence against restructuring | `contrary_strength` 0–1 | score × −0.8 | Part of probability |
| All four contributions | Starting prior of 12%, then weighted additions/subtraction | None after manual scoring | Raw log-odds | Sigmoid conversion | Rounded probability + separate 0.48 confidence + immutable evidence hashes |

```text
Frozen company and cutoff
          |
          v
Selected pre-cutoff issuer disclosure
          |  automated download/text extraction where available;
          |  manual fallback handling for many records
          v
Human reads pages and writes an evidence observation
          |
          v
Human assigns four 0-to-1 scores
          |
          v
Automated validation of dates, fields, and score grid
          |
          v
Rules 1.0.0 deterministic calculation
          |
          v
365-day restructuring probability
          |
          v
Immutable SQLite and portable JSON prediction record
```

## Three real frozen prediction traces

These examples were selected solely by their frozen predicted probabilities. No post-cutoff outcomes were researched or inspected.

### Relatively high: Forterra, cutoff 31 December 2024

**Frozen probability: 0.685156; confidence: 0.48**

Source evidence:

- Forterra Annual Report 2023, available date recorded as 25 March 2024.
- Cited pages: 2, 5, 7, 9, 10, 82, 87, 88, 93, 94, 95, and 100.
- The observation records a severe housing downturn, demand down about 30%, factory mothballing, restructuring and redundancy costs, revenue down 24%, EBITDA down, margin declining from 22.8% to 18.8%, cash use rather than generation, and sharply higher net debt.
- The 2023 mothballing, output reductions, redundancies, and related costs were marked as already announced, so they could not themselves count as the future outcome.

Manual extraction and features:

| Feature | Value | Contribution |
|---|---:|---:|
| Pressure language | 0.95 | +1.330 |
| Margin pressure | 0.95 | +0.855 |
| Cash pressure | 0.95 | +0.665 |
| Contrary strength | 0.10 | −0.080 |

Trace:

`−1.992430 + 1.330 + 0.855 + 0.665 − 0.080 = 0.777570`

`sigmoid(0.777570) = 0.685156`

Plain English: PIOTW rated this relatively high because the reviewed report described severe, quantified pressure across operations, margins, and cash, with little strong evidence pointing the other way. The known 2023 action was excluded as an outcome, although its existence still contributed to the pressure assessment.

### Around the middle: Computacenter, cutoff 31 December 2020

**Frozen probability: 0.129270; confidence: 0.48**

Source evidence:

- Computacenter Annual Report 2019, available date recorded as 9 April 2020.
- Cited pages: 6, 44, 52, 58, and 60.
- The observation records project, margin, utilization, and investment-backlog problems in FusionStorm, with plans to restore performance. It also records strong offsets: group services margin improved by 248 basis points, profit before tax rose 23.8%, operating cash flow was £200.2m, and net funds rose to £137.1m.

Manual extraction and features:

| Feature | Value | Contribution |
|---|---:|---:|
| Pressure language | 0.40 | +0.560 |
| Margin pressure | 0.10 | +0.090 |
| Cash pressure | 0.05 | +0.035 |
| Contrary strength | 0.75 | −0.600 |

Trace:

`−1.992430 + 0.560 + 0.090 + 0.035 − 0.600 = −1.907430`

`sigmoid(−1.907430) = 0.129270`

Plain English: the model saw a contained operating problem, but strong group-level profit, margin, cash, and balance-sheet evidence nearly cancelled that pressure. The result stayed close to the 12% starting prior.

### Relatively low: Softcat, cutoff 31 December 2022

**Frozen probability: 0.068982; confidence: 0.48**

Source evidence:

- Softcat Annual Report and Accounts 2021, available date recorded as 25 October 2021.
- Cited pages: 3, 30, 31, 35, 116, and 119.
- The observation records revenue growth of 7%, gross-profit growth of 17%, operating-profit growth of 27%, higher gross and operating margins, 90% cash conversion, and a debt-free position. Pandemic adaptations and supply responses were identified as already-existing context.

Manual extraction and features:

| Feature | Value | Contribution |
|---|---:|---:|
| Pressure language | 0.05 | +0.070 |
| Margin pressure | 0.05 | +0.045 |
| Cash pressure | 0.05 | +0.035 |
| Contrary strength | 0.95 | −0.760 |

Trace:

`−1.992430 + 0.070 + 0.045 + 0.035 − 0.760 = −2.602430`

`sigmoid(−2.602430) = 0.068982`

Plain English: PIOTW rated this relatively low because the report showed little pressure and unusually strong, quantified counter-evidence across growth, margins, cash, and debt.

## Pressure and Expansion

Neither `Pressure` nor `Expansion` exists as a calculated variable in PIOTW Rules 1.0.0. Rules 1.0.0 directly calculates only a restructuring-announcement probability.

The repository separately contains an Evidence Model 0.2 demonstration and broader specifications using operational-pressure and expansion/transformation concepts. Those components are not connected to the 289 frozen predictions. The honest description is: the restructuring experiment is one narrow first experiment relevant to the future Pressure idea; it is not itself the Pressure model, and it says nothing about Expansion.

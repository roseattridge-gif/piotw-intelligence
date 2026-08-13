# Pilot preregistration v0.1

Frozen before inspecting any post-31-December-2021 outcomes.

## Research question

At 31 December 2021, does a transparent combination of externally observable operational evidence improve prediction of defined 18-month operational outcomes over simple financial baselines?

## Cohort and pilot

The 30-name candidate frame is a purposive sector frame of UK-listed operating companies in industrial, manufacturing, engineering, aerospace, automotive, materials and industrial-technology subsectors. It is not claimed to be a statistically complete exchange census. Names are included without reference to post-cutoff outcomes. The pilot is selected by SHA-256 of a fixed seed plus ticker, taking the lowest hash in each of three broad strata. The script and complete candidate list are committed alongside this protocol.

## Information cutoff

Prediction date: **31 December 2021**. A document is eligible only if its evidenced public availability date is on or before the cutoff. Reporting period dates never substitute for public availability. Where only a month is known, use the month's final day; where availability is genuinely ambiguous, exclude.

## Prediction horizon and labels

Primary horizon: 18 months, ending 30 June 2023. Binary labels are independently verified from dated primary disclosures.

1. `material_restructuring`: quantified or explicitly material restructuring, site closure/consolidation, or group-wide cost programme.
2. `margin_deterioration`: reported adjusted operating margin falls by at least 150 basis points year-on-year.
3. `margin_recovery`: reported adjusted operating margin rises by at least 150 basis points year-on-year.
4. `material_inventory_correction`: inventory falls by at least 15% or the company announces an explicit material normalisation/correction programme.
5. `major_transformation_programme`: board-approved, named group-wide ERP, data, digital or operating-model programme.
6. `profit_warning`: company explicitly states results/profit will be materially below prior expectations.
7. `senior_leadership_change`: CEO or CFO departure/appointment, excluding already-announced succession before cutoff.
8. `major_capacity_investment`: announced capacity investment representing at least 2% of latest reported annual revenue or explicitly described as a major strategic capacity expansion.

## Predictions

The v0.1 operational model predicts the probability of **any material operational intervention or deterioration label** (1, 2, 4, 5, 6 or 8) within 18 months. It also records condition-specific rationales. Recovery and leadership change are evaluated separately and do not count as the primary composite unless the prediction explicitly names them.

## Baselines

1. Operating-margin deterioration: positive if latest margin is at least 100 bps below the prior comparable period.
2. Inventory/revenue divergence: positive if inventory growth exceeds revenue growth by at least 10 percentage points.
3. Financial stress count: margin deterioration, negative free cash flow, and inventory/revenue divergence, mapped to `(count + 1) / 5`.
4. Sector-relative deterioration: pilot-company financial-stress score above the pilot median (descriptive only at n=3).
5. Base rate: leave-one-company-out observed primary-label rate; random predictions use a fixed seed only for sensitivity.

## Model and evaluation

Operational evidence contributions are deterministic and preserved individually. Primary descriptive outputs: Brier score, precision/recall at 0.5, ranking of the three companies, and lead time. At n=3 no claim of statistical significance, ROC-AUC superiority, proprietary alpha or generalisability is permitted. This pilot tests feasibility and produces estimates for a larger preregistered backtest.

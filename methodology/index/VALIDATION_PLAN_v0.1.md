# PIOTW Index Validation Plan v0.1

**Status:** PRE-REGISTRATION SCAFFOLD / NO VALIDATION RESULTS  
**Methodology version:** 0.1.0

## Readiness claim

The framework is not production-ready. A real PIOTW Rating may be published only after point-in-time data, targets, methodology and evaluation windows are frozen in advance; leakage checks pass; results replicate; and the tests below demonstrate useful, stable incremental value. Passing registry validation is necessary but says nothing about score accuracy.

## Outcomes

Candidate adverse outcomes are restructuring announcement, profit warning, site closure, major cost programme, material headcount reduction, impairment, exceptional restructuring charge, margin deterioration, CEO/CFO/COO departure, disposal, covenant/distress event and insolvency. Positive candidates may include sustained margin improvement, evidenced productivity delivery, successful capacity ramp and completed transformation with realised benefits.

Every target needs an exact definition, materiality threshold where relevant, horizon, event date and information-available date, source hierarchy, adjudication procedure, duplicate-event rule and sector applicability. Targets already public at the prediction cutoff are ineligible.

## Required tests

1. **Discrimination:** rank and classification metrics with uncertainty; can the index distinguish later events?
2. **Calibration:** observed event rates by score/pressure band, calibration plots and error metrics; do worse scores correspond to higher adverse-event rates?
3. **Lead time:** performance by horizon and time from first signal to outcome.
4. **Stability:** sensitivity to reporting-cycle noise, copied wording, source removal and small evidence changes.
5. **Incremental value:** nested/time-split comparisons against all declared baselines.
6. **Sector robustness:** performance, calibration and missingness by sector/business model.
7. **Time robustness:** rolling-origin and out-of-time tests across different regimes.
8. **Feature redundancy:** correlations, clustering, ablation and contribution stability.
9. **Missing-data sensitivity:** disclosure propensity, simulated source loss and alternative coverage gates.
10. **Human-review burden:** review minutes, disagreement, escalation rate and throughput.

Also test cohort membership stability, transformation sensitivity, rating-band usefulness, confidence calibration, inter-reviewer agreement and fairness to low-disclosure companies. Report negative and null results.

## Baselines

Required candidates are EBITDA-margin trend, revenue growth, leverage, working-capital deterioration, share-price drawdown where appropriate and point-in-time available, a simple keyword-count model, sector median, random prediction and majority class. PIOTW must demonstrate out-of-sample incremental information beyond the relevant simple financial baselines; complexity alone is not value.

## Study design safeguards

- Use temporal splits and a final untouched out-of-time test set; do not randomly mix future and past disclosures.
- Preserve evidence → event → feature → immutable prediction → outcome separation.
- Fit transformations, imputation choices, cohort rules, weights and thresholds only on training data.
- Use point-in-time company universe and financial data to avoid survivorship and revision leakage.
- Predeclare exclusions and report coverage, class balance and confidence intervals.
- Evaluate company-level grouping so the same company does not leak across folds where inappropriate.
- Freeze hashes of corpus, labels, feature registry, config and code before each validation run.
- Treat n=1, synthetic and fixture results only as infrastructure demonstrations.

## Minimum publication gate

Before “PIOTW Rating” is permitted, the construct and target taxonomy must be reviewed; extraction reliability and evidence lineage must be acceptable; cohort sizes must meet the displayed precision rule; discrimination and calibration must replicate out of time; incremental value must beat relevant baselines; sector/time/missingness sensitivity must be understood; rating bands and confidence displays must be calibrated; operational review burden must be viable; and limitations/model card/versioned artefacts must be public. Numeric thresholds for these gates are deliberately unresolved and must be predeclared before validation, not chosen after seeing final results.

## Deliverables for every future validation run

Frozen manifest and hashes; preregistered protocol; cohort flow; target adjudication log; feature coverage; baseline and PIOTW metrics with uncertainty; calibration and lead-time results; ablations; sector/time slices; leakage audit; review-burden report; limitations; and explicit go/no-go decision.

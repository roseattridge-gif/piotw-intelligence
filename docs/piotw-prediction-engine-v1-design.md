# PIOTW Prediction Engine v1 Design

> **DESIGN ONLY — MODEL 2 HAS NOT BEEN TRAINED**

## Scientific ladder

The intended methodological progression is: univariate signal analysis; simple logistic regression; regularised logistic regression; tree/boosting comparison where justified; survival/time-to-event models where useful; and longitudinal/time-series methods only when data depth supports them. Each stage must earn its complexity through out-of-sample discrimination, calibration, Brier score, PR/AUC where appropriate, lift, lead time, stability and incremental value over conventional financial information.

Future prediction work should compare four separately frozen experiments:

| Experiment | Inputs | Question |
|---|---|---|
| A | frozen manual Rules 1.0.0 | benchmark performance of the original experiment |
| B | objective issuer-report features | do structured report facts outperform the manual baseline? |
| C | outside-in operational features | do operational sources work without issuer reporting? |
| D | B + C | does outside-in evidence add incremental value? |

No step should begin until its evidence inputs meet a predeclared readiness gate.

## Registry objects

A model experiment records cohort/partitions, outcome and horizon, feature allow-list, cutoff rules, missingness policy, training procedure, calibration, metrics and frozen hashes. Each prediction records model version, feature snapshot IDs, probability, generated time and evidence coverage. Outcomes are stored separately and joined only for authorised evaluation.

## Evaluation

Primary evaluation should include discrimination, calibration and decision usefulness: ROC-AUC/PR-AUC where appropriate, Brier/log loss, calibration slope/intercept, confidence intervals, lift at predeclared review capacities and comparator performance. Always report denominators, company clustering and temporal splits.

## Anti-leakage boundaries

- Register predictions before adjudicating outcomes.
- Keep development, validation and holdout partitions immutable.
- Enforce information-available-at cutoffs.
- Do not select features, prompts or thresholds using validation/holdout outcomes.
- Group related company occasions to avoid identity leakage.
- Preserve missingness and source coverage as explicit metadata.

## LLM boundary

An LLM can assist evidence extraction under a frozen contract. It cannot see outcomes, choose predictive features, assign coefficients, generate probabilities or replace evaluation. Model probabilities must come from a separately versioned statistical/rules experiment with inspectable inputs.

## Current status

Rules 1.0.0 remains the only frozen prediction experiment. Evidence Engine 0.3.4 is not technically frozen after its live semantic gate result, and official Model 2 readiness remains **NOT READY**.

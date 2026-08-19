# Evidence Engine 0.2 — frozen Model 2 readiness gate

Status: frozen before aggregate Evidence Engine 0.2 benchmark calculation.

This gate evaluates evidence quality only. It authorizes no predictive training and uses no restructuring outcomes.

## READY FOR MODEL 2 DEVELOPMENT

All of the following must be met:

- complete numerical observation accuracy ≥ 90%;
- metric identity accuracy ≥ 95%;
- reporting-period and current/comparative-role accuracy ≥ 95%;
- currency, unit, scale, and sign accuracy each ≥ 97%;
- adjusted/statutory identity accuracy ≥ 95%;
- evidence-span correctness and end-to-end provenance completeness each ≥ 98%;
- event precision ≥ 90%, recall ≥ 80%, and F1 ≥ 85%;
- severe-error rate ≤ 2%;
- longitudinal feature correctness ≥ 90%;
- manual correction rate ≤ 30%;
- difficult-report complete numerical accuracy ≥ 80%;
- jobs discovery precision/recall ≥ 90% where measurable;
- job function accuracy ≥ 85%, seniority and location accuracy ≥ 90%;
- false job-closure rate caused by collection failure = 0%;
- no protected Rules 1.0.0 artefact changes.

## READY WITH HUMAN REVIEW

All of the following must be met, but at least one full-readiness condition above is missed:

- complete numerical observation accuracy ≥ 80%;
- metric and period identity accuracy ≥ 85%;
- provenance completeness ≥ 95%;
- event precision ≥ 80% and recall ≥ 65%;
- severe-error rate ≤ 5%;
- longitudinal feature correctness ≥ 80%;
- manual correction rate ≤ 50%;
- difficult-report numerical accuracy ≥ 65%;
- jobs discovery/classification measures ≥ 75% and false closure from a recorded outage = 0%;
- no protected Rules 1.0.0 artefact changes.

## NOT READY

Use this status if any human-review minimum is missed, the real/gold corpus is materially incomplete, severe errors exceed 5%, provenance cannot be audited, jobs outages create false closures, or a protected artefact changes.

## Decision rules

- Rates must include integer numerators and denominators.
- An observation is completely correct only when metric, value, sign, unit, scale, currency, period, period role, accounting basis, and provenance all match.
- Missing gold observations are false negatives, not silently excluded.
- Extra observations are false positives where the benchmark defines an exhaustive document/metric scope.
- Difficult-report performance is reported independently and cannot be hidden by the ordinary-report average.
- If manual gold verification is incomplete, the status is automatically `NOT READY` regardless of machine scores.
- The gate must not be edited after benchmark aggregation except to repair a documented evaluator bug; any such change requires a new gate version.


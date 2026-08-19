# Evidence Engine 0.3.1 event-context hardening

## Methodological boundary

This is engineering against a frozen AI-assisted development benchmark, not independent validation. Every benchmark row is `formal_gold=false` and `admissible_for_model2_gate=false`. Official readiness remains **NOT READY**.

## Failure taxonomy and changes

The 78-case benchmark records hypothetical risk, biography, third-party context, historical/completed events, negation, taxonomy overreach, duplication, wrong entity, generic boilerplate and ambiguous evidence. The extractor now preserves candidate events separately from context assessments and final events.

Generalisable fixes include explicit negation and modality rules, actual-condition overrides, biography/accounting exclusion patterns, target-company anchoring, planned/current/historical status, segment/facility scope, expanded phrase-to-taxonomy mapping, multi-label atomic events and semantic duplicate suppression. No issuer-specific extraction exception was introduced.

Numerical normalization now preserves capex exactly as reported and separately stores its positive economic magnitude. Accounting basis is restricted to `statutory`, `adjusted`, `company_defined` or `unclear`; unlabeled values are not presumed statutory.

## Remaining risks

Dense tables and broken PDF reading order can produce fragments that lack enough context. Historical restructuring-cost tables remain difficult to distinguish from current interventions without reliable table headers and period binding. The fresh sample is development QA, not accuracy evidence.

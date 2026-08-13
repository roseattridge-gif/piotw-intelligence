# PIOTW restructuring validation v2 plan

Frozen design work began: 13 August 2026
Status: protocol construction; no v2 outcome adjudication has begun

## Existing evidence boundary

Validation v1 is preserved and reproducible. Running the v1 registration and evaluation scripts regenerated the tracked prediction and result JSON byte-for-byte (`fa376af…` and `de61f17…`) and all 18 repository tests passed. V1 contains ten companies, cutoffs at 31 December 2021 and 31 December 2022, 20 prediction occasions and four known positives. Because those outcomes have been inspected, every v1 occasion is development data in v2.

V1 predictions were committed in `a4ca5b8` before outcome inspection. Outcome resolution and reporting were committed in `9ef109b`. V1 artefacts will not be overwritten or relabelled by v2.

## Candidate model carried forward

`restructuring-rules-1.0.0` is the frozen candidate. Its operative behaviour is:

- target: a previously unannounced material restructuring within 12 months;
- prior: 0.12;
- inputs on the closed interval 0–1: `pressure_language`, `margin_pressure`, `cash_pressure`, `contrary_strength`;
- log-odds weights: 1.40, 0.90, 0.70 and -0.80 respectively;
- probability: logistic(logit(0.12) + weighted inputs), rounded to six decimal places in the portable prediction record;
- missing inputs: invalid; no silent zero imputation;
- confidence: 0.48 for the v1 one-primary-disclosure extraction pattern, separate from probability;
- one structured evidence extraction per v1 occasion, ordered evidence identifiers, deterministic extraction/snapshot hashes;
- already-announced programmes excluded from future outcomes;
- prediction identity: ticker, cutoff and model version.

The machine-readable specification will become the sole parameter source without changing these results. Regression tests will compare all 20 probabilities, contributions and evidence hashes with the committed v1 fixture.

## Known limitations

- The four inputs are manually assessed ordinal scores, not yet independently duplicated.
- V1 source hashes cover structured extraction and metadata, not every full source file.
- Only one researcher adjudicated v1 outcomes.
- Financial and language comparator thresholds were specified after v1 outcome inspection.
- Twenty repeated occasions are too small for statistical validation.
- A 0.5 threshold produces no positives; the model is evaluated as probability/ranking output.
- The purposive 30-company candidate frame is not a complete exchange census.

## V2 design

1. Treat v1 as development only.
2. Freeze the complete candidate-model specification, outcome contract, five comparator specifications, cohort rules, partitions and three-level gate before inspecting new outcomes.
3. Form a deterministic approximately 100-company UK-listed industrial cohort with stable identity and historical primary disclosures. Selection cannot use later restructuring outcomes.
4. Use three cutoffs per eligible company: two validation cutoffs and one later untouched temporal holdout. The proposed dates are 31 December 2020, 31 December 2022 and 31 December 2024. The 2022 occasions for the ten v1 companies remain development and are not rescored as validation. The 2024 horizon ends 31 December 2025 and is complete at protocol freeze.
5. Preserve full source bytes where retrieval and terms permit; otherwise record URL, dates, retrieval status, hashes and the preservation limitation.
6. Register features and predictions in an immutable v2 store, then commit them before generating adjudication material or examining outcomes.
7. Export outcome packets with probabilities, ranks, contributions and comparator outputs removed. Support two independent reviewers, uncertainty and explicit reconciliation.
8. Evaluate validation and holdout separately. Do not use either to tune version 1.0.0, baseline probabilities, alert thresholds or exclusions.
9. Use company-clustered bootstrap intervals and company/sector/cutoff sensitivity. Keep adjacent outcomes separate from the restructuring label.
10. Generate the complete report and machine-readable results through `make validate-restructuring-v2`.

## Freeze sequence

The required order is: specifications → manifests → pre-cutoff evidence → immutable predictions → Git checkpoint → masked outcome packets → adjudications → evaluation. The v2 runner must refuse to evaluate a partition whose manifest, model, comparator, evidence or prediction hash differs from its frozen registry.

No dashboard, SaaS or unrelated prediction work is in scope.

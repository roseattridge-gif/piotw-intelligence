# Evidence Engine 0.3.6 fresh validation protocol

Status: preregistered design; **not executed**; founder authorisation still required.

## Eligibility and contamination

The gate must use 7–14 entirely unused companies and 14–28 entirely unused documents. Company name, ticker, document ID, URL and source hash must not overlap 0.3.4, 0.3.5, 0.3.6 development, prior blinded packs or AI review sets.

`scripts/check_evidence_v036_contamination.py` scans repository CSV evidence and fails on any overlap. The proposed manifest currently contains headers only. Populating it does not authorise execution.

## Balanced source-first set

Every family must contain at least:

- 12 supported candidate opportunities;
- 12 difficult negatives;
- six genuinely ambiguous cases.

The set must include attribution, temporal, polarity, hypothetical, historical, fragment, heading-only and accounting-only traps. Source-first labels are created and hashed before provider execution. Reviewers see source context, not model decisions.

## Frozen gate

| Measure | Requirement |
|---|---:|
| Accepted-event precision | ≥ 90% |
| Supported-event retention | ≥ 80% |
| Severe false positives | 0 |
| Attribution errors | 0 |
| Provenance completeness | 100% |
| Provider/schema/contract completeness | ≥ 99% |

The gate runs once. No tuning follows inspection. Failure is preserved and execution stops. Passing the technical gate does not change official Model 2 readiness or substitute for later independent cross-review.

The frozen machine-readable protocol is `config/evidence/fresh_validation_protocol_v0_3_6.json`.


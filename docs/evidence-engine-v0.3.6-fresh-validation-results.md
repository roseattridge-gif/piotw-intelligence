# Evidence Engine 0.3.6 fresh validation results

## Decision

`EVIDENCE_ENGINE_0_3_6_FRESH_VALIDATION_FAILED`

The single preregistered run failed the frozen precision and supported-event-retention thresholds. The result is preserved. There was no tuning and there will be no rerun on this set. Evidence Engine 0.3.6 is not frozen as a technically ready extractor.

## Gate result

| Measure | Result | Frozen requirement | Pass |
|---|---:|---:|---|
| Accepted-event precision | 43.75% (7/16) | at least 90% | No |
| Supported-event retention | 8.33% (7/84) | at least 80% | No |
| Severe false positives | 0 | 0 | Yes |
| Attribution errors | 0 | 0 | Yes |
| Provenance completeness | 100% | 100% | Yes |
| Provider/schema/contract completeness | 99.05% (208/210) | at least 99% | Yes |

The final decisions comprised 16 accepts, including 7 supported accepts and 9 false positives, plus 68 ambiguous decisions. There were no severe false positives and no attribution errors.

## Results by event family

| Family | Precision | Retention | Supported retained | False positives |
|---|---:|---:|---:|---:|
| Delivery, capacity and sites | 0% | 0% | 0/12 | 0 |
| Demand and growth | 50.00% | 25.00% | 3/12 | 3 |
| Leadership change and execution | 16.67% | 8.33% | 1/12 | 5 |
| Quality and regulatory | 0% | 0% | 0/12 | 0 |
| Restructuring and cost action | 66.67% | 16.67% | 2/12 | 1 |
| Supply-chain resilience | 100% | 8.33% | 1/12 | 0 |
| Workforce | 0% | 0% | 0/12 | 0 |

The principal failure is excessive rejection/ambiguity of genuinely supported events, combined with poor precision in demand and especially leadership/change cases. The fail-closed architecture prevented severe and attribution errors, but at an unusably high retention cost.

## Provider execution

- OpenAI Batch ID: `batch_6a845c08125c81908e68b99e8b0f5498`
- Model: `gpt-5-mini`
- Requests received: 210/210
- Completed and contract-valid: 208/210
- Input tokens: 242,401
- Output tokens: 197,426
- Total tokens: 439,827
- Estimated Batch cost: $0.227726125
- Request-manifest SHA-256: `59772a04dbf77a94585e74c52bfb0660c0d5a8ca0b14cd40d8fca75145935639`
- Result SHA-256: `2838a18466d3245f4b84e0c4f894c316a5784a06380d4258dda8f74f282c18bf`

The frozen semantic prompt, evidence-pointer transport, taxonomy, family contracts and thresholds were not tuned before or after the run.

## Boundaries and next status

- Outcomes accessed: no
- Model 2 trained: no
- Rules 1.0.0 artefacts changed by this run: no. The full test suite exposed an existing test-side-effect: `tests/test_restructuring_v2_evidence_builder.py` rebuilds the frozen evidence CSV using the locally installed `pypdf` patch version. The resulting parser-version-only drift was immediately restored to the registered frozen bytes. The final guard verifies all 12 protected files.
- Evidence Engine 0.3.6 frozen: no
- Official Model 2 readiness: `NOT READY`

No further fresh gate or scientific execution is authorised on this corpus.

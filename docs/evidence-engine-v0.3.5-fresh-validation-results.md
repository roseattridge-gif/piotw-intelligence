# Evidence Engine 0.3.5 fresh validation results

Status: `EVIDENCE_ENGINE_0_3_5_FRESH_VALIDATION_FAILED`

The preregistered gate was executed exactly once as OpenAI Batch `batch_6a841f001edc81908f64fb7b47aa647a` using `gpt-5-mini`, the frozen 0.3.5 prompt, existing taxonomy, strict schema and immutable evidence-pointer transport. The one-run ledger prevents a retry.

| Measure | Result | Frozen threshold |
|---|---:|---:|
| Candidates | 156 | — |
| Provider-valid/schema-contract-valid | 155/156 | complete execution required |
| Accepted events | 70 | — |
| Precision | 50/70 = 71.43% | ≥95% |
| Supported-event retention | 50/111 = 45.05% | ≥90% |
| False positives | 20 | — |
| Severe false positives | 7 | 0 |
| Attribution errors | 1 | 0 |
| Provenance completeness | 70/70 = 100% | 100% |

One response was incomplete at the frozen 2,000-output-token ceiling and therefore failed parsing closed. Total use was 182,898 input tokens and 173,784 output tokens; estimated Batch cost was $0.19665.

The result is a scientific failure, not a provider-only result: even excluding the incomplete response, precision, retention, severe-false-positive and attribution thresholds all failed. No tuning or rerun was performed. The extractor is not frozen, no cross-review pack was created, and official Model 2 readiness remains `NOT READY`.

The most important technical pattern is over-rejection of genuine factual statements combined with continued acceptance of cost increases as growth, product/program naming as cost reduction, and customer-related restructuring as target-company restructuring.


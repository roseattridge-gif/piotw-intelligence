# Evidence Engine 0.3.4 Batch API results

## Provider execution

- Synthetic preflight: `MODEL_BATCH_PROVIDER_PREFLIGHT_PASSED`
- Scientific Batch: 685/685 provider requests completed; 0 provider failures
- Structured decisions accepted by the frozen local validator: 489
- Candidate results rejected by the frozen local validator: 196
- Incomplete because the 2,000-token ceiling was reached: 8
- Completed responses rejected for schema/semantic-contract violations: 188
- Batch ID: `batch_6a83017941f481909f300700dd40f935`

The principal completed-response failures were unsupported evidence spans,
decision/reason-code inconsistencies, unsupported event remaps, or direct-support
claims on non-accepted decisions. These are preserved as candidate-level
failures. They were not repaired, retried, or tuned.

## Frozen gate result

The scientific gate failed closed as
`MODEL_PROVIDER_EXECUTION_FAILURE_BATCH`, because only 489 of 685 candidate
outputs passed the existing structured semantic validator. The partial replay
reported 94.74% precision and 62.07% supported-event retention on the brand-new
unseen inspection set, with 0 severe false positives, 0 attribution errors, and
100% provenance completeness among accepted inspected events. These are partial
diagnostics, not a passing gate result.

Total provider usage, including failed local validations, was 446,701 input
tokens and 536,749 output tokens (983,450 total; 407,296 reasoning tokens).
Estimated Batch API cost using the configured Batch prices was USD 0.592586625.

The extractor was not frozen and no cross-review pack was created.

Official Model 2 readiness remains **NOT READY**. Batch execution does not use
restructuring outcomes, does not train Model 2, and cannot change the formal
human-readiness decision.

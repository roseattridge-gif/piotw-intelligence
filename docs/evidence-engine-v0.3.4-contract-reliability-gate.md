# Evidence Engine 0.3.4 contract-reliability gate

Frozen before live development smoke testing on 17 August 2026.

This gate measures provider and structured-contract reliability only. It does
not measure semantic accuracy and is not admissible for Model 2 readiness.

## Required conditions

- provider request completion: 100%
- strict JSON-schema-valid output: at least 99%
- locally contract-valid output: at least 98%
- truncation rate: 0%
- systematic parser or response-extraction rejection: none
- evidence-span validation: every accepted response resolves to an exact span
  from the supplied source context
- no unresolved local-validator inconsistency in the smoke sample

All conditions must pass on the predeclared synthetic/development smoke set.
The model remains `gpt-5-mini`; `max_output_tokens` remains fixed at 2,000.

Pass status: `SEMANTIC_CONTRACT_RELIABILITY_PASSED`.

Failure status: `SEMANTIC_CONTRACT_RELIABILITY_FAILED`.

Passing this gate permits only a methodology assessment of whether the failed
scientific Batch may be rerun unchanged. It does not itself authorize or pass
the scientific semantic-quality gate.

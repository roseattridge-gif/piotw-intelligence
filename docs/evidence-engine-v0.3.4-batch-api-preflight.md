# Evidence Engine 0.3.4 Batch API preflight

## Preserved first attempt

The original 500-token synthetic preflight is preserved under
`data/derived/evidence_engine_v0_3_4_batch/preflight/`. Both provider requests
completed, but the synthetic REJECT response was truncated and its JSON could
not be parsed. No scientific Batch was submitted.

## Mechanical execution repair

The rerun uses `max_output_tokens: 2000`, recorded in
`config/evidence/semantic_batch_execution_v0_3_4.yaml`. This is an execution
ceiling change only. The provider, model, prompt, JSON schema, taxonomy,
candidate construction, deterministic rules, samples, thresholds, and gate are
unchanged.

The rerun is isolated under
`data/derived/evidence_engine_v0_3_4_batch/preflight_2000/`. Parser records now
retain response status, incomplete details, and reasoning-token usage so a
provider truncation is diagnosable without exposing credentials.

The scientific Batch may be prepared and submitted only after both synthetic
ACCEPT and REJECT cases complete, parse, validate, and match their expected
decisions.

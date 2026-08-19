# Evidence Engine 0.3.4 semantic-contract failure analysis

Source Batch: `batch_6a83017941f481909f300700dd40f935`. The original
raw outputs, hashes, manifests, usage, and failed-closed result remain unchanged.

## Complete breakdown

| Primary failure | Count | Share of 196 | Diagnosis |
|---|---:|---:|---|
| Accept evidence span not present exactly in context | 72 | 36.73% | Model output failure |
| PDF-control/Unicode exact-span comparison defect | 37 | 18.88% | Local validator bug |
| Accept paired with a non-accept reason code | 32 | 16.33% | Model cross-field failure |
| Reject/ambiguous asserted direct evidence support | 32 | 16.33% | Model cross-field failure |
| Ambiguous paired with a non-ambiguous reason code | 13 | 6.63% | Model cross-field failure |
| Truncated at 2,000 output tokens | 8 | 4.08% | Provider/model output-budget failure |
| Unsupported event remap | 2 | 1.02% | Model cross-field failure |

Overall: 159 model/output failures and 37 objective local-validator failures.
No missing-field, wrong-type, invalid-enum, extra-prose, response-extraction, or
provider request failures were observed. The eight malformed JSON results were
all responses explicitly marked incomplete because `max_output_tokens` was
reached.

## Token analysis

Valid responses used a median 667 output tokens (p90 995; p95 1,097.8; maximum
1,927), including a median 512 reasoning tokens. Completed but contract-invalid
responses used a median 827 output tokens (p90 1,273.5; p95 1,566.4; maximum
1,943), including a median 640 reasoning tokens. Every truncated response used
exactly 2,000 output tokens; reasoning usage ranged to 704 tokens and had a
median of 480.

Contract-invalid responses were therefore longer on average, but most failures
were cross-field or evidence-copy failures rather than truncation.

## Structured Outputs and SDK finding

The installed client is OpenAI Python SDK 3.1.0. Requests used the Responses API
with `text.format.type = json_schema`, `strict = true`, all fields required,
nullable unions for optional values, enumerated decisions/statuses/reason codes,
and `additionalProperties = false`. Strict provider schema enforcement was
active: completed responses were structurally valid JSON matching those
individual field constraints.

The integration defect was that a flat schema could not enforce relationships
between fields. For example, it allowed `decision = accept` together with a
historical-only reason code. Exact evidence containment is inherently a local
semantic/provenance check and cannot be guaranteed by a static general schema.

## Mechanical reliability repair

The response now contains one `result` object whose value is a supported nested
`anyOf` across accept, reject, and ambiguous branches. Each branch contains the
same nine frozen decision fields with unchanged meanings, but provider schema
validation now enforces:

- decision-appropriate reason-code sets;
- `evidence_supported = true` only for accept;
- null evidence span for non-accept decisions;
- an exact source candidate span for accept decisions;
- candidate-specific allowed event types/remaps.

The local parser unwraps `result` before applying the unchanged semantic
validator. No model, taxonomy, candidate, deterministic rule, benchmark,
threshold, or semantic decision meaning changed. The output ceiling remains
2,000 tokens.

## Development smoke result

The predeclared 12-case Batch smoke test failed the reliability gate:

- provider completion: 11/12 (91.67%);
- strict-schema-valid: 11/12 (91.67%);
- locally contract-valid: 11/12 (91.67%);
- truncation: 0/12;
- development Batch cost: USD 0.007123125.

All eleven provider-completed cases passed both the strict schema and unchanged
local contract. The remaining request failed before inference with HTTP 400
`invalid_json_schema`: the provider rejected an escaped quotation mark embedded
in the candidate-specific exact-span string enum. This proves that arbitrary
source text cannot safely be embedded as a strict-schema enum literal.

Status: `SEMANTIC_CONTRACT_RELIABILITY_FAILED`.

The scientific gate was not rerun. A future separately authorised mechanical
repair should replace the unsafe literal enum with a source-safe evidence
pointer that resolves locally to immutable exact source text, then repeat a
fresh development-only reliability smoke test.

The machine-readable diagnosis is in
`data/derived/evidence_engine_v0_3_4_contract_failures.json`; all 196 development
regression cases are preserved in
`data/evidence_engine_v0_3_4/semantic_contract_regression_cases.jsonl`.

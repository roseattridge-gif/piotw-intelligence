# Evidence Engine 0.3.4 evidence-pointer repair

Status: development transport repair; not independent validation. Official Model 2 readiness remains **NOT READY**.

## Problem

The first contract-reliability smoke embedded each candidate's literal evidence text in a strict JSON Schema enum. Quotes and other PDF-derived characters could make the provider reject the schema before the model produced a decision. This was a transport defect, not a scientific result.

## Repair

Each candidate now receives one deterministic, ASCII-only `span_<sha256>` identifier plus `span_none`. The strict provider schema contains only those safe identifiers. The request manifest stores an immutable local mapping from the identifier to the exact source text, source evidence ID, offsets, text hash and occurrence count. After provider output, PIOTW resolves the identifier locally and then applies the unchanged semantic contract validation.

The original semantic prompt, model (`gpt-5-mini`), taxonomy, decision meanings, candidate generation, deterministic filters, samples, thresholds and `max_output_tokens: 2000` remain unchanged. A separate mechanical transport instruction tells the provider which identifier to return; it does not alter the meaning of accept, reject or ambiguous.

## Integrity rules

- Unknown or cross-candidate identifiers fail closed.
- Accept must use the candidate source identifier.
- Reject and ambiguous must use `span_none`.
- The resolved text, offsets and SHA-256 must still match the immutable candidate context.
- Literal source text is absent from the provider JSON Schema.
- Repeated identical spans use the lowest exact offset and record the total occurrence count.
- The request manifest preserves the complete provenance chain.

## Verification plan

Local tests cover straight and curly quotes, backslashes, newlines, tabs, control characters, Unicode, long PDF-like spans, unknown pointers, cross-candidate resolution, duplicate occurrences and end-to-end resolution before local contract validation. All local tests, lint and the 12-artifact frozen isolation guard must pass before the one permitted paid development smoke.

The paid smoke is exactly 12 non-scientific cases. Its frozen reliability thresholds are: provider completion 100%, schema validity at least 99%, local contract validity at least 98%, truncation 0%, no unknown pointers or systematic parser rejection, and exact evidence resolution for accepted decisions. Passing this smoke only permits a methodology decision about rerunning the unchanged scientific gate; it does not itself change readiness or authorise predictive modelling.

## Scientific boundaries

No restructuring or holdout outcomes are accessed. No Model 2, Pressure score or Expansion score is trained or created. The prior Batch job and failed smoke remain preserved. Rules 1.0.0 and its protected artefacts are unchanged.

## Execution result

`SEMANTIC_CONTRACT_RELIABILITY_PASSED` on 17 August 2026.

- Batch: `batch_6a83232874f08190bc48eddb7b00b7a7`
- Provider completion: 12/12 (100%)
- Strict-schema-valid output: 12/12 (100%)
- Local-contract-valid output: 12/12 (100%)
- Accepted responses resolving to exact evidence: 7/7 (100%)
- Unknown pointers: 0
- Truncations: 0/12
- Input tokens: 11,428
- Output tokens: 7,205
- Estimated Batch cost: USD 0.0086335

This establishes that the repaired provider contract is mechanically reliable on the predeclared development smoke. It does not establish semantic accuracy. Under the frozen contract-reliability protocol, the pass permits only a methodology assessment of whether the unchanged scientific Batch may be rerun; it does not itself authorise that rerun. No scientific gate was run, the extractor was not frozen, and no cross-review pack was created.

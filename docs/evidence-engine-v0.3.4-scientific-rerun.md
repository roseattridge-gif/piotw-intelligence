# Evidence Engine 0.3.4 scientific semantic-quality rerun

Execution type: `SCIENTIFIC_SEMANTIC_GATE_RERUN_AFTER_MECHANICAL_CONTRACT_REPAIR`

Authorised on 17 August 2026 after the source-safe evidence-pointer contract smoke passed all frozen reliability thresholds.

## Scientific invariants

This rerun uses the identical 685-candidate scientific set from the preserved prior Batch `batch_6a83017941f481909f300700dd40f935`. Candidate identity and order must match its immutable request manifest exactly. The model remains `gpt-5-mini`; the semantic prompt meaning, taxonomy, event and reason-code meanings, deterministic candidate and exclusion rules, context/history/table/entity rules, benchmark and unseen samples, inspected rows, semantic-quality thresholds and `max_output_tokens: 2000` are unchanged.

The sole mechanical transport change is the already-tested deterministic evidence pointer. Raw literal evidence is absent from provider JSON Schema enums; the local manifest preserves the exact source text, immutable hash, offsets and source evidence identifier. PIOTW resolves the returned pointer before applying the unchanged local semantic contract.

## Execution controls

- New immutable directory: `data/derived/evidence_engine_v0_3_4_batch/scientific_rerun_pointer_v1`
- Endpoint: `/v1/responses`
- Completion window: `24h`
- Exactly one provider request per candidate
- Exactly one scientific Batch submission
- Cost guard: less than USD 5
- Partial outputs cannot be used for tuning
- Insufficient contract reliability yields `MODEL_PROVIDER_EXECUTION_FAILURE_BATCH` and no semantic interpretation
- A semantic pass yields `TECHNICALLY READY FOR BLINDED CROSS-REVIEW`; any mandatory failure yields `NOT TECHNICALLY READY`

No restructuring or holdout outcomes may be accessed. No Model 2, Pressure score or Expansion score may be created. Official readiness remains `NOT READY` regardless of this gate until the later cross-review/readiness decision.

## Pre-submission record

The first preparation attempt stopped before submission because candidate membership was identical but sequence order differed. Following fresh authorisation, candidates were mechanically aligned to the preserved manifest order by immutable candidate identity. Regression tests prove that alignment changes only sequence and rejects membership drift.

- Candidate count and unique identities: 685/685
- Exact membership and order match: yes
- Unique deterministic custom IDs: 685/685
- Raw source spans embedded in provider schemas: 0
- Input JSONL SHA-256: `92ec9aa7f7289d1d51bee6d1404fc64d2c1d0099e452d38c59f5a352dff6c393`
- Candidate manifest SHA-256: `4201940d863101458a524f5e70c12c7b9d8fed4963bdecace1994adbc9dba5b9`
- Prompt SHA-256: `a243352f9e75a050d9467cf501d9a0ecfa2827d72f94ff0f27a0b872e2092f27`
- Schema SHA-256: `96649cd457ed49a8a6fd4da457ad375e0dc53a32a2dc82455ec9b7cb55cc1b9c`
- Taxonomy SHA-256: `d304d385649b341ba5d2394f77fd8dfc91fccce9822fb34b54372a791a372d6c`
- Deterministic/verifier config SHA-256: `d04c6ef8d0a527de0729436b8c365c0f5b7781ec680d78924e301ac3adaa8f31`
- Evidence-pointer config SHA-256: `7c3923342f8827046731db1b2d07e4c3db85f05ef1088a63d3bdbf6ede7659f9`
- Evidence-pointer transport SHA-256: `f8a23d888a4a513179ee58993fd64fdfca4807ba55936052247efd25ca7d8ad9`
- Repository commit: `eac7499a8ea659e126036675f773471a3d3451f6`
- Model and ceiling: `gpt-5-mini`, 2,000 tokens
- Conservative maximum cost: USD 1.42485725 (below USD 5 guard)
- Tests: 178 passed
- Lint: passed
- Protected artefacts: 12 unchanged

The single rerun was submitted as Batch `batch_6a832dbf3d2c81909c2ff50f828be0da`. No second Batch was submitted.

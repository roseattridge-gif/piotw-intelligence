# Evidence Engine 0.3.6 fresh source-first labels

## Frozen label set

The final frozen set contains 210 real-source candidate spans. Each of the seven event families contains exactly 30 cases: 12 supported, 12 unsupported and 6 ambiguous.

| Event family | Supported | Unsupported | Ambiguous | Total |
|---|---:|---:|---:|---:|
| Delivery, capacity and sites | 12 | 12 | 6 | 30 |
| Demand and growth | 12 | 12 | 6 | 30 |
| Leadership change and execution | 12 | 12 | 6 | 30 |
| Quality and regulatory | 12 | 12 | 6 | 30 |
| Restructuring and cost action | 12 | 12 | 6 | 30 |
| Supply-chain resilience | 12 | 12 | 6 | 30 |
| Workforce | 12 | 12 | 6 | 30 |

Files:

- Candidates: `data/evidence_engine_v0_3_6/fresh_frozen_candidates.jsonl`
- Labels: `data/evidence_engine_v0_3_6/fresh_ai_source_first_labels.csv`
- Freeze manifest: `data/evidence_engine_v0_3_6/fresh_label_candidate_freeze.json`
- Candidate SHA-256: `3ceb6cadf9a2f5245076d70fbdbdf26362f2768786c3808a678dd8b10d8fec42`
- Label SHA-256: `86b87296102cf8b035a14d6726c5a1755f835cbacf90e2d928a26ff7af29996a`
- Label/candidate freeze SHA-256 recorded by the gate: `cf05460543e55fdf2db127d6341270cf40967767d934188b14249442687ab424`

## Methodological status

Labels were created source-first, before semantic-verifier inference, and then frozen. They are explicitly tagged `AI_ASSISTED_FINOPS_REVIEW`, `formal_independent_human_gold=false`, and `admissible_for_model2_gate=false`.

The review Batch returned 451 valid structured reviews and 27 incomplete outputs. The balanced freeze used valid reviews, real-source sparse-context ambiguous cases and one source-first unsupported adjudication where the review response was incomplete. No review request was rerun.

These labels are suitable for the authorised technical gate, but they are not independent human validation and cannot satisfy the official Model 2 readiness gate.

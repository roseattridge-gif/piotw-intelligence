# Evidence Engine 0.3.7 AI-finops development comparison

## Methodological boundary

The 36 answers are tagged `AI_ASSISTED_FINOPS_REVIEW` and `formal_independent_human_gold=false`. They are development-contaminated fixtures, not independent truth. The comparison therefore tests contract integration and deterministic validation behaviour; it is not an extraction-accuracy claim.

## Development replay results

| Measure | Result |
|---|---:|
| Cases | 36 |
| Reviewer YES | 33 |
| Reviewer AMBIGUOUS | 2 |
| Reviewer NO | 1 |
| Factual-YES contract agreement | 33/33 |
| NO contract agreement | 1/1 |
| Ambiguity contract agreement | 2/2 |
| Exact provenance validity | 36/36 |
| Timing field transport | 36/36 |
| Entity-relation transport | 36/36 |

These perfect replay figures are expected because the uploaded review supplies the semantic fixture output. They prove that 0.3.7 can preserve the reviewed atomic fact through schema and provenance validation; they do not show how accurately a live model would produce the same fields from new evidence.

Twenty-four factual observations marked YES in the review had been rejected or left ambiguous by 0.3.6 and now survive the observation-first contract. Examples include historic executive appointments, realised restructuring actions, sales-volume changes, supply conditions and regulatory settlements. This supports the architecture hypothesis that early family assignment discarded otherwise auditable facts.

Ambiguous cases remain `HRV1-004` and `HRV1-007`. The accounting-only `HRV1-020` remains rejected. No family mapper or outcome model was used.

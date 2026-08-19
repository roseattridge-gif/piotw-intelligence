# Evidence Engine 0.3.6 failure decomposition

## Scope and status

This is a post-failure diagnostic on the scientifically spent 0.3.6 corpus. The corpus is now `DEVELOPMENT_CONTAMINATED` and may never again be described as unseen validation. No provider call, outcome lookup, model fitting or 0.3.6 rerun was performed.

The row-level record is `data/derived/evidence_engine_v0_3_6_failure_decomposition.csv`. It covers every unique candidate involved in at least one requested failure class:

- 77 missed supported events;
- 9 false positives;
- 68 final ambiguous decisions;
- 107 unique rows after overlaps are removed.

Every frozen label was selected from the 478 candidates produced by `fresh_broad_source_locator_v1`. Therefore every labelled row was surfaced. This benchmark cannot measure facts that candidate generation never surfaced because no independent source-level annotation searched for those missing facts.

## Missed supported events

| Primary blocking stage | Count | Share of 77 misses |
|---|---:|---:|
| Family-specific contract returned reject/ambiguous | 57 | 74.03% |
| Shared deterministic safety rule rejected | 10 | 12.99% |
| Local contract accepted but semantic verifier rejected/ambiguous | 8 | 10.39% |
| Provider execution incomplete | 2 | 2.60% |

Thus 67 of 77 misses (87.01%) were blocked locally before the semantic decision could produce a final accept. This does not mean the semantic model was never run; it means the final AND-gate could not accept regardless of the semantic answer.

The largest family-contract failure reasons were:

- quality/regulatory event not entailed: 12;
- workforce event not entailed: 11;
- delivery/capacity event not entailed: 9;
- change/execution event not entailed: 9;
- restructuring/action identity not entailed: 6;
- supply condition not entailed: 6.

No family-routing mismatch was observed because the benchmark labels inherited the family implied by the surfaced candidate event type. That is a circularity warning, not proof that routing is correct.

## False positives

All 9 false positives passed both the deterministic family contract and semantic verifier.

- 8/9 were labelled historical. The architecture had no reliable report-date-relative timing normalisation, so both layers accepted a factual but out-of-scope historical statement.
- 5 of those 8 were historical executive appointments.
- 1 was a completed restructuring action.
- 2 were demand rows with additional identity/polarity questions: production-driven sales-volume growth and declining regulatory-credit revenue proposed as `growth_language`.
- 1/9 was valuation boilerplate containing assumed sales growth rather than an observed operating condition.

The false positives are therefore joint failures: the deterministic contract did not enforce the label contract's time/identity boundary and the semantic model accepted factual wording without consistently testing that same boundary.

## Ambiguous decisions

The 68 ambiguous decisions were concentrated in Leadership/Change (15), Workforce (14), Delivery/Capacity (11), Quality/Regulatory (11) and Restructuring/Cost Action (11). Of these:

- 44 were already blocked by family-contract ambiguity;
- 21 were non-supported/ambiguous labels handled without a false accept;
- 3 had a locally accepted candidate but an ambiguous semantic decision.

Ambiguity was safe but excessive. It protected precision at the cost of making the extractor operationally uninformative.

## Label-contract conflict

The source-first labels materially complicate interpretation:

- 45/84 supported labels are marked `historical`;
- 4/84 supported labels are marked `hypothetical`;
- 68/84 supported labels have `hypothetical_or_historical=true`;
- the frozen family contracts generally accept only current, ongoing or planned events.

This does not turn the failed gate into a pass. Even among the 35 supported rows whose timing field is current, ongoing or planned, only 2 were finally accepted. It does mean the exact allocation between model failure and label-definition failure cannot be trusted until a qualified human resolves a targeted slice.

## Conclusion

The dominant measured recall bottleneck is the family-contract layer, not the semantic model. The precision failures show that duplicating event meaning across a regex contract and semantic prompt does not guarantee consistent timing, identity or polarity. The present architecture asks both layers to decide too much, while the benchmark labels themselves do not consistently apply the written temporal boundary.

# Evidence Engine architecture options after 0.3.6

| Option | Recall | Precision | Explainability/provenance | Maintainability | Cost | Semantic-drift risk | Assessment |
|---|---|---|---|---|---|---|---|
| A. Current family-first design | Low in the fresh gate | Poor despite fail-closed design | High provenance, but reasons split across two decision layers | Poor; regex and prompt semantics duplicate | Medium | Medium | Reject. It produced 74% of misses at the family-contract stage and nine joint false accepts. |
| B. Broad candidates → shared factuality check → family classification | Higher | Potentially good | Strong if factuality output retains exact pointers | Better than A | Medium | Medium | Viable intermediate design, but still risks treating event families as the extraction target. |
| C. Observation-first extraction → validated atomic observation → downstream family links | Highest controllable recall | Potentially best after validation/review | Strongest: one fact, one provenance chain, multiple non-duplicating links | Best conceptual separation | Medium | Low-to-medium | Recommended foundation. It aligns with PIOTW's existing raw evidence → observation → event principle. |
| D. Constrained LLM subject/action/object/timing extraction → deterministic mapping | High | Depends on schema and validation | Strong if evidence pointers and fail-closed validation remain mandatory | Good, with model-version discipline | Highest of four, but Batch-manageable | Highest if model output is treated as truth | Use as a component within C, not as the whole architecture. |

## Recommendation

Adopt **Option C with a constrained Option D extraction component**.

The semantic model should extract or reject a proposed atomic factual observation. It should not directly decide an ontology dimension or final event family. Deterministic code should validate schema, provenance, dates, units and allowed states, then map accepted observations into one or more event-family relationships.

This preserves Option C's clean intellectual object while using the model only where language understanding is needed. It avoids an opaque end-to-end classifier and avoids the current duplication of brittle family regexes with semantic event adjudication.

## Compatibility with the ontology

The eight dimensions remain useful as product/navigation concepts. They should be links from canonical observations, not extraction labels. For example, one fact—“the company closed its Leeds plant in June”—can remain one observation while linking to Delivery & Capacity, Cost & Productivity and Change & Execution without duplicating the evidence record.

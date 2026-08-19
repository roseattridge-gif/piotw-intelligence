# Evidence Engine 0.3.7 independent labels

Status: **AWAITING INDEPENDENT HUMAN ANNOTATION**

Reviewers work only from the supplied official filing. They must not see PIOTW zones, extractions, model decisions, event families, dimensions, scores or predictions.

For each document, identify every material sentence or bounded passage that establishes a small factual operational observation. Record one row per observation. Copy the shortest exact evidence span that still establishes who or what is affected, what happened, its actuality and timing. Do not infer missing facts.

- Use `YES` only when the source establishes the fact.
- Use `NO` only for a specifically reviewed passage that does not establish a factual operational observation.
- Use `AMBIGUOUS` when the source genuinely cannot support a stable decision.
- Preserve historical, planned and hypothetical statements using the timing field; do not silently convert them to current realised facts.
- Attribute customer, supplier, competitor and industry statements to those entities, not to the issuer.
- Do not assign event families, PIOTW dimensions or significance.

The blank CSV schema is authoritative. Reviewer identity and annotation timestamps are required. Completed files must be returned independently and frozen before comparison.


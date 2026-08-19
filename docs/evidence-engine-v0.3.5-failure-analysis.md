# Evidence Engine 0.3.5 failure analysis

Status: frozen scientific failure, analysed only as `DEVELOPMENT_CONTAMINATED_NOT_VALIDATION`.

## What failed

The one permitted fresh gate contained 156 candidates from five companies and ten documents. One provider response was incomplete. Of 155 valid responses, the generic verifier accepted 70: 50 supported and 20 unsupported. Precision was 71.43%; supported-event retention was 50/111 (45.05%). Seven false positives were severe, one was an attribution error, and provenance completeness was 100%.

The row-level matrix is [evidence_engine_v0_3_6_failure_matrix.csv](../data/derived/evidence_engine_v0_3_6_failure_matrix.csv). It records all 20 false positives and 61 false negatives without changing the frozen result.

## Root-cause matrix

| Root cause | What happened | Architecture implication |
|---|---|---|
| Subject ambiguity / insufficient support | 54 supported candidates were rejected under these two broad reasons | A single generic sufficiency test is too blunt; sufficiency must be defined per event family. |
| Actuality or timing | 11 errors involved hypothetical/historical framing | Retain shared deterministic actuality/timing checks before family adjudication. |
| Polarity and event identity | Five severe cost-growth statements were labelled as demand growth | Each family needs its own subject, measure and direction contract. Lexical “growth” is not an event. |
| Product/programme naming | “Cost Reduction Initiative” appeared as a name without proving a company cost action | Family logic must distinguish names from actions. |
| Third-party attribution | A customer's restructuring was attributed to the issuer | Attribution must be resolved before semantic acceptance. |
| Provider truncation | One response was incomplete | Continue fail-closed provider handling; do not count the candidate as accepted. |

## Conclusion

The failure is not primarily a transport, schema or provenance failure. Those components worked. It is an event-semantics architecture failure: the generic prompt tries to apply one notion of factual sufficiency to event types whose identities, directions and acceptable evidence differ materially.

The result does not support further generic prompt tuning. The appropriate next step is a shared evidence/attribution envelope followed by explicit event-family contracts. All examples in this analysis are contaminated development material and cannot be reused as unseen validation.


# Evidence Engine 0.3.6 architecture decision

## Decision

Adopt a hybrid event-family architecture.

1. Deterministic collection, immutable evidence text, offsets, hashes and candidate generation remain shared.
2. Shared prechecks resolve target attribution, actuality/timing, malformed evidence and minimum provenance.
3. A candidate is routed to an explicit event family.
4. The family contract determines what constitutes the event, permitted polarity, scope and sufficient support.
5. A narrow semantic adjudicator may operate inside that contract later; it may not invent events or override provenance.
6. All accepted events return to one canonical event schema and can link to multiple ontology dimensions without duplicating the fact.

This rejects both extremes: one universal semantic adjudicator is not precise enough, while fully separate pipelines would duplicate provenance, attribution, provider and storage logic.

## Alternatives considered

| Option | Precision/retention | Cost | Testing and maintenance | Decision |
|---|---|---|---|---|
| Continue tuning one generic verifier | 0.3.5 showed severe identity/polarity errors and broad over-rejection | Lowest prompt count | Simple superficially, but interactions across event types are hard to isolate | Rejected |
| Fully separate extractor per event type | Could be precise | High implementation/provider cost | Excessive duplication and drift across 47 atomic types | Rejected |
| Shared envelope plus event families | Separates identity/polarity while retaining common controls | Moderate and controllable | Contract tests are local; common infrastructure stays singular | Selected |

## Representative development proof

Only two families are implemented, using the contaminated 0.3.5 corpus:

- `demand_growth`
- `restructuring_cost_action`

Across 118 routed contaminated cases, the deterministic proof produced 83 true accepts, 25 true rejections, two false accepts and eight missed supported events. Demand/Growth had 73 true accepts, 11 true rejections and two false accepts. Restructuring/Cost Action had ten true accepts, 14 true rejections and eight missed supported events.

These are engineering diagnostics, not accuracy claims. They show that family-specific contracts can remove the known severe cost-growth, product-name and customer-attribution cases without requiring another scientific set. They also show that restructuring phrasing remains too varied for a deterministic final classifier.

## State and boundaries

- Evidence Engine 0.3.4 and 0.3.5 remain preserved failed versions.
- No fresh validation was run.
- No Model 2, Pressure, Expansion, benchmark or overall score was created.
- Official readiness remains `NOT READY`.
- The next scientific gate must use preregistered, genuinely unused evidence after more event families are implemented and development-tested.


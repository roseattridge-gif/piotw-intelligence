# Evidence Engine 0.3.7 observation architecture

## Status

`DEVELOPMENT ONLY — NOT SCIENTIFICALLY VALIDATED`

0.3.7 is a new namespace. It does not modify or reinterpret failed versions 0.3.4–0.3.6 and does not consume outcomes.

## Implemented flow

`source text → broad evidence zones → constrained semantic observation → deterministic validator → ACCEPT / REJECT / AMBIGUOUS atomic observation`

Evidence-zone selection uses operational language and quantitative/directional changes to find bounded passages. It deliberately does not assign event families or product dimensions.

The semantic interface answers one question: does the bounded evidence establish an atomic factual operational observation? A factual answer contains subject, action/state, object, timing, polarity, scope, entity relationship and an exact evidence span. The semantic layer cannot assign dimensions, event families, scores or predictions.

The deterministic validator:

- requires complete subject/action/object fields for a factual observation;
- requires the evidence span to exist exactly in the supplied source zone;
- preserves historical observations as factual and tagged `HISTORICAL`;
- preserves committed plans and hypothetical statements distinctly;
- converts unclear factual attribution to `AMBIGUOUS`;
- fails closed on incomplete or ungrounded output.

One canonical observation may later link to multiple event families and ontology dimensions. Those relationships are intentionally not implemented here.

## Contracts

- atomic observation: `config/evidence/atomic_observation_v0_3_7.schema.json`
- evidence zone: `config/evidence/evidence_zone_v0_3_7.schema.json`
- implementation: `evidence_engine_v0_3_7/`

The exact evidence text, offsets, source ID, immutable source hash and version metadata remain part of every observation.

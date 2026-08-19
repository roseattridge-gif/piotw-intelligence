# Evidence Engine 0.3.7 proposal

## Status

`PROPOSED_NOT_IMPLEMENTED`

0.3.7 should be an observation-first evidence extractor. This document does not authorise implementation or validation.

## Proposed pipeline

`document segmentation → high-recall evidence zones → constrained atomic observation extraction → deterministic validation → accepted/rejected/ambiguous observation → deterministic family/dimension links → longitudinal features later`

## Responsibilities

### Candidate generation

Surface bounded evidence zones with high recall. Use headings, sentences, table rows/headers and broad operational/numeric cues. Do not assign a final event family or positive/negative event identity.

### Semantic model

From one bounded evidence zone, return structured subject/action/object/timing/polarity/scope and an exact evidence pointer, or return `NO_FACT`/`AMBIGUOUS`. It may normalise wording but may not invent an observation, company, date, magnitude or causal claim.

### Deterministic rules

Validate pointer membership, source hashes, schema, dates, units, target-entity resolution, explicit negation/hypothetical status and allowed enumerations. Preserve the semantic record and fail closed when the evidence pointer or required fields are invalid. Deterministic rules should validate facts, not re-interpret each event family through regexes.

### Family routing

After an observation is accepted, map its typed predicate, object, direction and scope to event families and ontology dimensions. Permit multiple relationship links without copying the canonical observation. Unknown mappings go to review; they do not become silently accepted events.

## Observation and event distinction

An observation is what the source establishes: for example, `facility X closed`, `backlog declined 12%`, or `CFO appointed effective 1 May`. An event is a versioned downstream classification or grouping of one or more observations. Ontology dimensions are product relationships, not source facts.

## Context contract

Provide:

- exact candidate sentence/table row;
- immediately preceding and following sentence where available;
- nearest section heading;
- relevant table title and column headers;
- issuer, publication date and reporting period;
- a bounded maximum of approximately 2,000 characters unless a table structure requires a versioned exception.

The model must identify the exact supporting substring by immutable pointer. A heading alone cannot support an observation.

## Ambiguity and fail-closed behaviour

- `ACCEPTED`: all mandatory factual fields and evidence pointer validate;
- `AMBIGUOUS`: plausible fact but subject, timing, scope, polarity or definition is unresolved;
- `REJECTED/NO_FACT`: hypothetical, negated, third-party-only, definitional, boilerplate or unsupported;
- provider/schema failures: no observation and retry only under a preregistered execution policy.

Ambiguous observations remain reviewable evidence records but cannot enter features.

## Development strategy

1. Freeze the 36-row human review before inspecting comparisons.
2. Turn the spent 0.3.6 corpus into development-only observation fixtures.
3. Test extraction fields separately: factuality, subject, actuality, timing, polarity, scope and evidence pointer.
4. Add source-zone/table fixtures and cross-family cases.
5. Require zero severe provenance/attribution errors and publish per-field confusion matrices.
6. Compare human-first and machine-assisted review burden.

## Future fresh gate

Preregister a new gate only after the human ambiguity review and development tests pass. Its source documents must be new. Gold annotation must begin at the document/source level so candidate-generation recall can finally be measured. Report two separate gates:

- observation extraction: recall, precision and field accuracy;
- downstream mapping: family/dimension mapping accuracy.

Do not use an AND-gate between duplicated regex and semantic event classifiers. Do not train Model 2 until the independent human readiness process permits it.

## Exact next build step

First conduct and freeze the 36-row blinded human review. Then, if authorised, implement only the 0.3.7 atomic observation schema, evidence-zone contract and deterministic validator against development fixtures. Do not build the family mapper or run a fresh gate until that extraction substrate passes its development checks.

# Evidence Engine 0.3.4 semantic adjudication

## Implemented flow

Raw report evidence → existing deterministic candidate generation → existing deterministic exclusions and context rules → constrained semantic verifier → accepted/rejected/ambiguous event.

The 0.3.3 pipeline remains responsible for parsing, candidate recall, entity attribution, negation, timing, hypothetical risk, tables, structural zones, duplicates, and provenance. Only its accepted remainder is routed to semantic adjudication. The verifier cannot invent events and operates on a small evidence-bound context.

Two providers implement the same interface:

- a deterministic development verifier and mock provider for reproducible tests;
- an OpenAI Responses API provider using strict structured output and `gpt-5-mini` by default.

The real adapter exists but was not invoked: no authorised API credential was present. Therefore all reported 0.3.4 diagnostics are deterministic development QA, not model-backed semantic validation.

## Audit and caching

The cache key contains hashes of the candidate span and local context plus taxonomy, prompt, and model versions. Changing any one invalidates reuse. Both the semantic output and final event carry hashes and version metadata. Invalid output fails closed.

## Scientific boundary

The benchmark is development-only, `formal_gold=false`, and inadmissible for the Model 2 gate. Formal human-gold, the repaired blinded pack, outcomes, predictions, and frozen baseline artefacts are untouched. Official readiness remains `NOT READY`.

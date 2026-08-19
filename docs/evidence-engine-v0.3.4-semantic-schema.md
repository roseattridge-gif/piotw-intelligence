# Evidence Engine 0.3.4 semantic schema

The verifier receives only the target company, proposed existing taxonomy event, exact candidate span, a local context window (maximum 2,400 characters), heading, publication date, and deterministic entity/timing metadata. It receives no outcomes, predictions, future evidence, or feature importance.

The output is strict JSON with: `decision`, `event_type`, `subject_type`, `event_status`, `scope`, `evidence_supported`, `exact_support_span`, `reason_code`, and `short_reason`. Decisions are `accept`, `reject`, or `ambiguous`. An acceptance is invalid unless its support span is copied exactly from the supplied context. A remap is permitted only to an existing taxonomy type pre-authorised for that candidate. Provider errors, invalid JSON, unsupported remaps, missing spans, and schema violations fail closed to `ambiguous`.

Accept reasons: `DIRECT_CURRENT_EVENT`, `DIRECT_ONGOING_CONDITION`, `DIRECT_PLANNED_EVENT`, `DIRECT_SEGMENT_EVENT`, `DIRECT_SUBSIDIARY_EVENT`.

Reject reasons include generic/hypothetical risk, third-party-only, biography, legal or cross-reference-only wording, headings, accounting definitions/measures, historical-only or negated statements, wrong entity/context, malformed fragments, and insufficient support. Ambiguity codes identify unresolved subject, timing, event type, or source fragments.

Each assessment preserves the deterministic routing decision, semantic decision, final decision, reason, provider/model/prompt versions, candidate and context hashes, exact support span, token counts, latency, cache key, and output hash.

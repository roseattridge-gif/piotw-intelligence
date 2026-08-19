# Evidence Engine 0.3.1 event-context rules

Status: development diagnostics only. These rules do not alter the frozen Evidence Engine 0.3 readiness gate.

The implemented flow is `text span -> candidate event -> context assessment -> accepted, rejected or ambiguous event -> deduplication`. Keyword presence creates only a candidate.

Each assessment records entity relevance, group/segment/facility/supplier scope, negation, hypothetical wording, timing, historical/completed wording, structural zone, decision reason and confidence. A final event retains its exact evidence span and candidate IDs.

## Deterministic decisions

- Explicit negation is rejected.
- Generic or hypothetical risk wording is rejected unless the same span gives evidence that the condition actually occurred.
- Completed or prior-period events are not promoted as current events.
- Biographies, definitions and recurring accounting boilerplate are rejected.
- Third-party-only events are rejected; unclear attribution is ambiguous.
- Plans remain `planned`, distinct from `current` and `ongoing`.
- One span may produce distinct atomic events, such as a strike causing both labour constraint and operational disruption.
- Same-type events with matching scope/period and highly overlapping evidence are deduplicated with a recorded link.

The local window is the matched sentence plus one neighbouring sentence on each side. This was chosen to recover nearby entity/timing context without combining remote report passages. Remaining risk: PDF text order and tables can still create malformed spans.

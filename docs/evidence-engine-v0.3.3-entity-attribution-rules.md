# Evidence Engine 0.3.3 entity-attribution rules

## Acceptance contract

An event is accepted only when the span supports a factual condition, an identifiable target-relevant subject, sufficiently clear timing, the asserted taxonomy mapping, direct provenance, non-generic status and non-duplicate identity.

Subjects are typed as target company, target segment, target subsidiary, joint venture, supplier, customer, competitor, industry, third party, former employer, acquisition target or unknown. Only the target company and clearly controlled segment/subsidiary subjects are accepted as company events. External subjects remain evidence context but are not promoted.

Local issuer pronouns (`we`, `our`, `the Company`, `the Group`) are resolved only after checking whether a supplier, customer, competitor, named third party, biography, joint venture or acquisition target is the grammatical subject. Segment and subsidiary scope is retained rather than promoted to group scope.

Relationship-aware extraction separates cause from impact. A supplier labour shortage remains supplier context; an explicitly stated disruption to company production may separately support a target operational-disruption event.

Risk status is typed as actual current, actual current with forecast, actual historical, planned, generic risk, hypothetical risk or ambiguous. Modal wording does not erase an embedded factual clause, but a conditional-only statement is rejected.

Unknown subject, unclear timing or unreliable joined text cannot be rescued by a numeric confidence score. Such candidates are rejected or held ambiguous.

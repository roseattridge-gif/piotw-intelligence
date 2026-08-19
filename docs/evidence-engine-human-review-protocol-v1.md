# Evidence Engine human ambiguity review protocol v1

## Purpose

This is a 36-case blinded, independent human review of atomic factual observations. It is designed to distinguish extractor failure from ambiguity or inconsistency in the AI-assisted 0.3.6 labels before any Evidence Engine 0.3.7 implementation.

It is not predictive validation, formal Model 2 gold, or permission to rerun 0.3.6.

## Review design

- Two independent reviewers, A and B, receive the same 36 cases in different frozen random orders.
- Reviewers receive anonymous case IDs, source document type, publication/reporting dates and bounded evidence context.
- Reviewers do not receive company identity unless it remains unavoidably present in the quoted source, candidate/event-family labels, PIOTW dimensions, AI labels, 0.3.6 decisions, expected answers or failure categories.
- Reviewers work from the supplied evidence only and must not research companies externally.
- Answers are made at atomic-observation level, not event-family or ontology level.
- Reviewer C adjudicates only material A/B disagreements after A and B files are complete and frozen.

## Frozen membership

Membership is frozen in `reviewer_pack_human_ambiguity_v1/internal_do_not_share/frozen_36_case_membership.json` before reviewer materials were generated. The 36 cases are the already-designed post-0.3.6 diagnostic slice; selection was not changed to favour a 0.3.7 answer.

The internal slice contains:

- historical vs current: 33;
- hypothetical vs actual: 4;
- planned vs realised: 8;
- issuer vs third party: 5;
- polarity ambiguity: 36;
- executive appointments: 6;
- restructuring/cost action: 5;
- demand/growth: 6;
- supply chain: 4;
- workforce: 5;
- capacity/sites: 4;
- quality/regulatory: 6;
- change/leadership: 6.

Category tags exist only in the internal freeze; reviewers cannot see them.

## Review outputs

Each reviewer completes every required field in their workbook or equivalent structured response. Responses must validate against `config/evidence/human_observation_review_response_v1.schema.json`. A `YES` answer additionally requires non-empty subject, action/state, object, timing, scope, entity relationship and exact evidence span. The evidence span must appear verbatim in the supplied context after whitespace normalisation.

## Independence and freezing

Reviewer A and B must not discuss cases or see one another's answers. On return, each file is copied unchanged into a dated intake directory, hashed and marked frozen before validation or comparison. Corrections after return require a separately versioned corrected response; the original remains preserved.

## Boundaries

No outcomes, predictions, Model 2, score, Pressure/Expansion construct or new validation corpus enters this review. The spent 0.3.6 corpus remains development-only.

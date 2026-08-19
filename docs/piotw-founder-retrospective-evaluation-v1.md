# PIOTW Founder Retrospective Evaluation v1

## Purpose

Founder retrospective lets Rose compare PIOTW's outside-in reconstruction with what she remembers from working inside the organisation. It is an evaluation layer only.

## Separation

The panel saves to a browser-local key scoped by entity and snapshot date. Records contain:

- `evidenceClass: FOUNDER_RETROSPECTIVE`
- `admissibleAsEvidence: false`
- selected evaluation labels
- free-text note
- save timestamp

No server endpoint, evidence-store write or feature calculation consumes this record.

## Available evaluations

- Broadly accurate
- Partly accurate
- Missed important issue
- Misleading
- False inference
- Important signal surfaced
- Surfaced too late
- Surfaced early

The free-text prompt is: “What was actually happening internally?”

## Future comparison protocol

If retrospective material is later exported, it must remain a separate labelled dataset. Comparison should occur only after the public reconstruction for that snapshot is frozen. Retrospective detail must never be used to rewrite the historical public-evidence chain or tune illustrative values and then be presented as an independent result.

# PIOTW atomic-observation reviewer instructions v1

## Your task

For each case, decide what the supplied passage factually establishes. This is factual interpretation, not company research, risk scoring or prediction.

Use only the evidence shown in the case. Do not search for the company, report, people or subsequent events. Do not infer facts that the passage does not state.

## Question A

Does the supplied evidence support a factual operational observation?

- `YES`: the passage establishes a real factual state, change, action or committed plan.
- `NO`: it is only hypothetical risk, negation, generic description, accounting definition, unsupported implication or unrelated material.
- `AMBIGUOUS`: the passage might establish a fact, but subject, meaning, timing, actuality or scope cannot be resolved from the supplied context.

## If you answer YES

Record:

- **subject:** who or what the statement is about;
- **action_or_state:** the factual action, condition or change;
- **object:** what was acted on or changed;
- **timing:** select one timing value below;
- **polarity:** direction of change where relevant;
- **scope:** group, segment, facility, geography, product, programme or other stated scope;
- **entity_relationship:** how the subject relates to the issuer;
- **exact_evidence_span:** the shortest verbatim passage that directly supports your answer.

## Timing values

- `CURRENT`: true at the stated reporting point.
- `ONGOING`: continuing over a period that includes the reporting point.
- `PLANNED_COMMITTED`: announced, approved or committed, but not yet completed.
- `COMPLETED_RECENT`: completed during the current/recent reporting period and presented as a current-period development.
- `HISTORICAL`: prior background or an older completed event.
- `HYPOTHETICAL`: possible, conditional or risk-only—not realised or committed.
- `UNCLEAR`: timing cannot be resolved from the supplied context.

Historical statements can still be factual: answer `YES` and label them `HISTORICAL` when the source clearly establishes the past fact. Hypothetical statements are not realised observations; normally answer `NO` and use `HYPOTHETICAL` where the template permits timing context.

## Entity relationship values

`ISSUER`, `SUBSIDIARY`, `CUSTOMER`, `SUPPLIER`, `COMPETITOR`, `INDUSTRY`, `OTHER`, or `UNCLEAR`.

Do not attribute a customer, supplier, competitor or industry fact to the issuer. A clearly identified consolidated subsidiary may be recorded as `SUBSIDIARY`.

## Planned versus possible

A plan is `PLANNED_COMMITTED` only when the passage says it was announced, approved, committed or otherwise adopted. Words such as “may”, “might”, “could”, “risk of” or “if” usually describe a possibility, not a committed action.

## Examples not present in this review

**Actual fact:** “The group permanently closed its Bristol depot in March.” → `YES`; action/state `closed`; object `Bristol depot`; timing depends on the report date.

**Hypothetical risk:** “A prolonged port strike could delay deliveries.” → `NO`; timing `HYPOTHETICAL`.

**Committed plan:** “The board approved construction of a second production line, due to open next year.” → `YES`; timing `PLANNED_COMMITTED`.

**Third party:** “A key supplier suspended production for two weeks.” → `YES`; entity relationship `SUPPLIER`; do not record the issuer as the subject.

**Ambiguous:** “Transformation remained a priority.” → `AMBIGUOUS` unless the context states a concrete programme, action or operational state.

## Final checks

- Complete all 36 cases.
- Do not assign PIOTW event families, dimensions, risk or scores.
- Use `AMBIGUOUS` rather than guessing.
- Keep the exact evidence span verbatim.
- Do not discuss your answers with the other reviewer.

# Evidence Engine human-review adjudication v1

## When adjudication occurs

Reviewer C is used only after Reviewer A and Reviewer B responses are complete, validated, hashed and frozen. No adjudication occurs in the pack-preparation phase.

## Automatic agreement

A case is automatically accepted without Reviewer C when A and B agree on:

- factual observation (`YES`, `NO` or `AMBIGUOUS`);
- timing, if both answer `YES`;
- entity relationship, if both answer `YES`;
- materially equivalent subject, action/state and object after case/whitespace normalisation;
- evidence spans that are identical or one is a direct contained refinement of the other.

Differences in reviewer notes or confidence alone are not material.

## Material disagreement

Send a case to Reviewer C if any of these apply:

- factual-observation values differ;
- one reviewer says `YES` and the other leaves a mandatory factual field unresolved;
- timing differs across current/ongoing/planned/recent/historical/hypothetical boundaries;
- entity relationship differs;
- subject, action/state, object, polarity or scope implies a materially different fact;
- evidence spans support different propositions or one span is not present in the supplied context;
- either reviewer identifies an evidence-pack defect.

## Reviewer C procedure

Reviewer C receives the same blinded case and the frozen A/B answers. Reviewer C does not see PIOTW output, AI-assisted labels, 0.3.6 decisions or diagnostic classifications. C selects A, selects B, or writes a new adjudicated atomic observation with a reason tied to the evidence and written contract.

Adjudicated answers are stored separately from A and B. Original reviewer files are never overwritten.

# PIOTW Multi-Family Condition Policy Review Protocol v0.1

Status: preregistered development-methodology review. This is not independent scientific validation.

## Purpose and boundary

This review asks whether current development policies for estate, leadership/organisation, procurement and careers produce reasonable operational-condition decisions across a broader source-first sample. It does not test predictive value. `scientific_gate_run=false`; frozen Evidence Engine documents, restructuring outcomes, holdout outcomes, Rules 1.0.0 and Model 2 are out of scope.

## Frozen runtime and policy

- Evidence envelope: `piotw-evidence-family-envelope-v0.1`.
- Multi-source engine: `piotw-multi-source-evidence-depth-v0.1`.
- Qualification policy: `piotw-condition-qualification-policy-v0.1-development`.
- Policy file and hash are recorded in `config/conditions/multifamily_review_protocol_v0_1.json` before evaluation.
- No threshold or candidate definition may change before the first review result is frozen.

## Company-selection rules

Include real companies only when all of the following hold:

1. the company is absent from the frozen restructuring cohort;
2. primary issuer or public-authority sources expose a defensible estate, leadership, procurement or existing careers history before the cutoff;
3. company and business-unit scope can be stated explicitly;
4. inclusion is based on source availability, not knowledge of a desired condition;
5. every result can be reproduced from recorded source spans and dates.

The frozen selected set is Kingfisher, Howden Joinery, Greggs, JD Wetherspoon, Kier Group, Mears Group and the existing Cloudflare careers-control case. The review needs at least six companies. Travis Perkins is rejected because it overlaps the frozen restructuring cohort and has already contaminated development policy. Wickes, Mitie, Capita and Serco are rejected for the same cohort-overlap reason. Companies without resolvable source history are recorded as rejected rather than replaced after results are known.

## Source-family inclusion rules

- Estate requires comparable site/branch/depot counts from primary issuer sources, ideally three periods, with entity and portfolio scope retained.
- Leadership requires a direct issuer or regulated announcement establishing an actual appointment, exit, role redesign or organisation change. Biography, rumour and generic succession language are excluded.
- Procurement requires a primary public notice naming an exact legal entity or an approved parent/subsidiary mapping. Notice versions and amendments must be deduplicated to the underlying award.
- Careers uses only stored cutoff-safe snapshots already approved by the careers pipeline.

## Candidate definitions

- `estate_expansion`: comparable estate count rises without simultaneous disclosed gross closure activity.
- `estate_contraction`: comparable estate count falls without simultaneous disclosed gross opening activity.
- `estate_reshaping`: comparable estate history includes both openings and closures or relocations, with net and gross movement retained.
- `organisational_restructuring`: a primary source establishes an operating-structure, reporting-line or senior-role design change. A routine appointment alone is factual evidence, not automatically restructuring.
- `procurement_activity_acceleration` / `deceleration`: deduplicated approved award-record counts change across comparable publication periods; public awards remain a partial activity view.
- Careers definitions are unchanged from the existing qualification policy.

## Review questions

For every candidate, inspect source evidence before the engine decision and answer: factual correctness; candidate reasonableness; entity scope; history; magnitude; persistence; independence of corroboration; contradiction handling; qualification reasonableness; finance/operations investigatory value; overstatement; and missed qualification.

Classify each result as `CORRECT_QUALIFICATION`, `CORRECT_WITHHOLD`, `FALSE_POSITIVE`, `FALSE_NEGATIVE`, `AMBIGUOUS_NEEDS_MORE_EVIDENCE`, `ENTITY_RESOLUTION_ERROR` or `FEATURE_POLICY_ERROR`.

## Predeclared readiness gate

The review scope must contain at least 12 candidate decisions, three estate companies with three comparable periods, three leadership companies with direct primary evidence, two procurement companies with approved entity resolution, and three families with real candidates. Otherwise Detect is `NOT_READY_INSUFFICIENT_REVIEW_SCOPE` regardless of apparent performance.

If scope is met, development readiness additionally requires: factual-observation accuracy at least 95%; entity-scope accuracy 100%; qualified-condition precision at least 90%; false-negative rate no more than 10%; ambiguous cases no more than 20%; provenance completeness 100%; zero severe false positives; zero unhandled contradictions; at least two family policies assessed stable; and no policy retired.

## Stopping rule

Run one review over the frozen selected set and cutoff. Do not add replacement companies, alter labels, change policy or rerun after aggregate results are visible. Ambiguous evidence stays ambiguous. Contradictory evidence stays visible. Policy revisions, if justified, are proposed only after the frozen result and are not used to rescore this review.

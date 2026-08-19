# PIOTW post-observation product layer

Status: **DESIGN ONLY — DO NOT IMPLEMENT BEFORE 0.3.7 INDEPENDENT VALIDATION PASSES**

The atomic observation is the factual substrate. Later product layers must reference it rather than copying or rewriting the fact.

## Layer A — observation-to-dimension relationships

One canonical observation may link to one or more of the eight approved operational dimensions. Relationships are versioned and auditable. They do not change the source evidence, create duplicate observations or imply significance. Ambiguous and rejected observations do not enter downstream layers.

## Layer B — longitudinal features

Versioned feature definitions derive only from accepted observations and point-in-time source records. The initial primitives are state, change, velocity, novelty and persistence. Every feature retains a chain back to its input observations and source evidence. Missing history remains missing; it is not imputed into a score.

## Layer C — peer benchmark

The benchmark is a separate engine. It compares like-for-like factual features using declared peer groups, periods and coverage rules. It must expose sample size and missingness. A benchmark does not become a company-health or risk score by default.

## Layer D — event prediction

Event prediction is a separate, preregistered engine trained only after the evidence substrate and feature definitions are ready. Predictions require a named event, horizon, calibrated probability, frozen inputs and immutable provenance. They must remain visually distinct from evidence and interpretation.

## Product boundary

No weights, composite scores, Pressure, Expansion, ranking or predictive meaning are authorised here. The next implementation decision follows the independent 0.3.7 observation-layer result.

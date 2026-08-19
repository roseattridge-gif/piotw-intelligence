# PIOTW company profile v1

## Implemented

The first truthful internal profile is available at `/intelligence/affirm` in `piotw-web`. It consumes the generated `company-intelligence-snapshot-v1` JSON and does not read analytical databases or recreate Evidence Engine logic in the frontend.

The profile shows:

- company and observation time;
- source families, freshness and health;
- all eight operational dimensions;
- factual state, change, velocity, novelty and persistence when present;
- exact source links and source hashes from the read model;
- a chronological factual feed;
- a deterministic “What changed?” summary;
- sparse, stale, failed and unresolved-source states;
- `NOT YET VALIDATED` for predictions, dimensions, benchmark and overall rating.

The real Affirm example currently has meaningful factual coverage only for Workforce & Capability, derived from two careers snapshots. The other seven dimensions are explicitly sparse. Procurement is displayed as unresolved and contributes zero company records because no supplier identity has been approved.

## Boundary

The Northstar fictional demonstration remains separate. The new internal route is the only current screen described as real stored PIOTW evidence. It calculates no peer percentile, PIOTW rating, Pressure, Expansion or prediction.

The generated frontend fixture is written by `scripts/build_company_intelligence_demo_v1.py` from the canonical read model, making it a deployable projection rather than a separately authored answer set.


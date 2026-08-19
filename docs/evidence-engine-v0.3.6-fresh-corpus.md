# Evidence Engine 0.3.6 fresh corpus

## Status

The single authorised 0.3.6 validation used 7 previously unused companies and 14 previously unused SEC filings: one 10-K and one 10-Q for each company. The companies were Amazon, Johnson & Johnson, Pfizer, Target, Tesla, Tyson Foods and Union Pacific.

The source pool was selected without reference to restructuring outcomes. A contamination check found no company, document, URL or source-hash overlap with the excluded 0.3.x development, diagnostic, blinded-review or AI-review sets.

## Frozen source pool

- Source manifest: `data/evidence_engine_v0_3_6/fresh_candidate_manifest.csv`
- Source artefacts: `data/evidence_engine_v0_3_6/fresh_sources/`
- Source-pool freeze: `data/evidence_engine_v0_3_6/fresh_source_pool_freeze.json`
- Companies: 7
- Documents: 14
- Report types: 7 annual reports and 7 quarterly reports
- Source-pool freeze SHA-256 recorded by the gate: `f8e9383ac5081d8cafdcff65d58a5afecd13c9f8649bf214ec11adedd6c08db6`

The broad deterministic locator produced 478 candidate spans before source-first review and balancing. It did not make the final semantic decision.

## Scientific boundaries

No restructuring or holdout outcomes were accessed. The corpus was not used to fit weights, train Model 2, or create Pressure, Expansion or an overall PIOTW score.

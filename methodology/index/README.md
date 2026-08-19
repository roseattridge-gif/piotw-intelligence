# PIOTW Index methodology artefacts

This directory contains the development-only PIOTW Index & Benchmark Framework v0.1. It defines constructs and deterministic registry contracts; it does not contain a scoring engine, peer data, benchmark distributions or company scores.

- `PIOTW_INDEX_SPEC_v0.1.md`: construct, taxonomy and transformation principles.
- `FEATURE_REGISTRY_v0.1.csv`: candidate feature contract.
- `DIMENSION_REGISTRY_v0.1.json`: six candidate dimensions.
- `PEER_BENCHMARK_SPEC_v0.1.md`: cohort hierarchy, disclosure and normalisation targets.
- `FINANCIAL_LINKAGE_REGISTRY_v0.1.json`: testable linkage hypotheses, not causal claims.
- `INTERVENTION_CLASS_REGISTRY_v0.1.json`: non-company-specific review taxonomy.
- `VALIDATION_PLAN_v0.1.md`: tests required before a real PIOTW Rating.
- `index-config.example.json`: versioned experimental configuration with no production scoring enabled.
- `schema/feature-definition.schema.json` and `types.py`: machine-readable/type contracts.

Run `python scripts/validate_index_methodology.py` or the dedicated pytest file to validate referential integrity and guardrails.

# ADR-001: Phase 0 is synthetic and local-first

Status: accepted. Build the full lineage and auditable UI with synthetic data before live collection. Keep PostgreSQL/Supabase compatibility but require no hosted service. Disable AI by default. This costs nothing, exposes architecture errors early and prevents synthetic results being confused with empirical validation.

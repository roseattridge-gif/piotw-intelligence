# Operational X-Ray implementation note

## Reused from PIOTW

- The existing Next.js App Router company experience, company header, and company navigation.
- The typed `lib/data` boundary used by the rest of the company product.
- Northstar Industrial's fictional company identity, reporting period, and 14 development-safe evidence observations.
- Exact source-document titles, dates, pages, evidence classifications, and confidence values for the observations referenced by ID in the X-Ray.
- The existing development-only Operational Index and Evidence Confidence concepts. No Evidence Engine, analytical methodology, or backend schema was changed.

## Frontend demonstration adapter

`lib/data/operational-xray.ts` exposes a frontend-facing `CompanyOperationalMap`. It deliberately isolates the product demonstration from production contracts. The following are illustrative rather than Evidence Engine outputs:

- the nine-stage operating archetype and its handoffs;
- stage and handoff pressure, materiality, and trend;
- value-trapped ranges and financial mechanisms;
- technology architecture, integration complexity, and digital-enablement score;
- customer themes, data maturity, ownership roles, and culture hypotheses;
- priority-hotspot ranking and causal propagation;
- volume estimates, customer-friction score, and unobserved diligence assumptions.

The interface labels these fields as `Illustrative demo`, `Modelled estimate`, `Strong inference`, `Hypothesis`, `Unknown`, or equivalent. Values are non-additive and not validated. Only signals with a `sourceEvidenceId` are treated as observed fixture evidence.

## Minimum future backend additions

Replacing the demonstration fields requires a versioned operational-map projection rather than changes to the Evidence Engine itself. The minimum additions are:

1. a company operating-archetype and stage/handoff registry;
2. evidence-to-stage and evidence-to-handoff relationships with classification and confidence;
3. governed operating-volume, technology, customer-theme, process-data, and accountability observations;
4. a validated financial-impact model with explicit assumptions, overlap handling, and lineage;
5. a causal-hypothesis contract that remains distinct from observed evidence;
6. a validated score/benchmark service before any rating is presented as production intelligence.

No external collector, scraping integration, database migration, or production scoring logic was added in this pass.

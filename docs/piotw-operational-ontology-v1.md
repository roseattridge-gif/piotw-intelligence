# PIOTW Operational Ontology v1

> **CANDIDATE PRODUCT ONTOLOGY — NOT YET EMPIRICALLY VALIDATED**

## Purpose

This ontology gives PIOTW a stable language for describing what can be observed inside and around a company. It is not a score, a model, or a claim that any item predicts an outcome.

The four levels are deliberately separate:

1. **Observation** — a source-supported fact, retaining time, units, scope and provenance.
2. **Signal** — a reproducible transformation of observations, such as change, velocity, novelty or persistence.
3. **Dimension** — a conceptual area used to organise related observations and signals.
4. **Outcome** — a separately adjudicated future event with an explicit horizon.

The machine-readable authority is `config/piotw_operational_ontology_v1.yaml`.

## Candidate dimensions

| ID | Dimension | Includes | Important boundary |
|---|---|---|---|
| `demand_growth` | Demand & Growth | orders, backlog, demand, volumes, market entry | expense growth and generic macro scenarios are not demand |
| `delivery_capacity` | Delivery & Capacity | throughput, utilisation, disruption, site/capacity changes | demand alone and hypothetical capacity risks are excluded |
| `cost_productivity` | Cost & Productivity | margins, cost base, productivity, efficiency | financing costs and metric definitions without action are excluded |
| `cash_working_capital` | Cash & Working Capital | cash flow, conversion, inventory, receivables, liquidity, leverage | accounting performance without a cash relationship is excluded |
| `workforce_capability` | Workforce & Capability | vacancies, labour availability, workforce actions, skills | biographies and prior-employer events are excluded |
| `supply_chain_resilience` | Supply Chain & Resilience | suppliers, materials, sourcing, logistics, recovery | global disruption without company exposure is excluded |
| `quality_customer` | Quality & Customer | defects, recalls, service quality, customer health | generic product-risk boilerplate is excluded |
| `change_execution` | Change & Execution | restructuring, transformation, footprint and investment programmes | aspirations, definitions and historical programmes presented as current are excluded |

## Coherence and overlap

The eight dimensions are coherent enough for a candidate ontology, but they are not mutually exclusive. A factual observation can legitimately map to more than one dimension. Capex can concern both delivery capacity and change execution; inventory can concern both working capital and supply resilience; redundancy can concern both workforce and change execution.

This overlap must remain explicit. PIOTW must not duplicate the underlying observation or count the same evidence repeatedly simply because it has several conceptual relationships. The canonical fact is stored once; dimension links are references.

The most fragile boundaries are:

- Demand versus Quality & Customer when weakness is customer-specific.
- Delivery & Capacity versus Supply Chain when an external constraint disrupts internal production.
- Cost & Productivity versus Change & Execution for cost-saving programmes.
- Workforce & Capability versus Change & Execution for reductions or reskilling.
- Delivery & Capacity versus Change & Execution for sites and capital projects.

## Directionality

Direction is metadata, not a prediction. Some values have a generally interpretable direction, such as higher operating margin or lower leverage. Others are inherently contextual. More capex could be expansion, catch-up maintenance or inefficient spending. More vacancies could reflect growth, churn or collection artefacts. Context-dependent measures must never be silently converted into favourable/adverse scores.

## Outcome boundary

Outcomes live outside the evidence ontology. Candidate outcome definitions cover restructuring, profit warnings, margin deterioration, workforce reduction, site closure, leadership intervention, capacity expansion, major investment, geographic expansion and operational disruption. Each requires an explicit horizon and independently sourced adjudication. Their presence in the ontology records possible future research relationships only; it does not establish predictive validity.

## Governance

- IDs are stable and machine-readable.
- Definitions, mappings and transformations are versioned.
- Raw evidence is immutable; corrections create reviewed versions.
- Missing means unknown, not zero.
- Ambiguous events remain ambiguous and do not silently enter features.
- No weights or coefficients belong in this ontology.
- Changes require a decision record, migration note and reference-integrity tests.


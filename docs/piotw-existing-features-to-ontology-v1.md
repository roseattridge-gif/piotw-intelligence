# Existing Evidence Engine Features → Candidate Ontology v1

> **CANDIDATE PRODUCT ONTOLOGY — NOT YET EMPIRICALLY VALIDATED**

## Inventory

Evidence Engine 0.1–0.3.4 defines 197 feature objects: nine numerical longitudinal features, four feature templates for each of 41 atomic events (164), and 24 jobs features. This document maps them; it does not endorse predictive value.

## Numerical longitudinal features

| Existing feature | Observation | Dimension |
|---|---|---|
| `revenue_yoy_change_pct` | revenue | Demand & Growth |
| `operating_margin_change_bps` | operating margin | Cost & Productivity |
| `free_cash_flow_change_pct` | free cash flow | Cash & Working Capital |
| `net_debt_change_pct` | net debt | Cash & Working Capital |
| `cash_conversion_change_bps` | cash conversion | Cash & Working Capital |
| `capex_growth_pct` | capex | Delivery & Capacity; Change & Execution |
| `restructuring_charge_change_pct` | restructuring charges | Change & Execution |
| `impairment_change_pct` | impairment charges | Cost & Productivity; Change & Execution |
| `exceptional_cost_change_pct` | exceptional costs | Cost & Productivity; Change & Execution |

## Atomic events

Each event currently generates count, mentions-change, new-appearance and persistence features.

| Dimension | Existing atomic events |
|---|---|
| Demand & Growth | demand weakness, destocking, customer weakness, geographic expansion, order-book strength, demand growth, recovery language, growth language |
| Delivery & Capacity | supply-chain constraint, labour constraint, operational disruption, capacity mismatch, footprint reduction, site closure, capacity reduction, capex growth, new facility, capacity expansion, geographic expansion, major investment |
| Cost & Productivity | loss-making unit, margin deterioration, inflation pressure, cost reduction, efficiency programme, margin improvement |
| Cash & Working Capital | cash deterioration, leverage increase, working-capital pressure, liquidity concern, refinancing, covenant concern, destocking, cash improvement, deleveraging, liquidity strength |
| Workforce & Capability | labour constraint, redundancy, workforce reduction, hiring, skills investment |
| Supply Chain & Resilience | supply-chain constraint, inflation pressure |
| Quality & Customer | customer weakness |
| Change & Execution | refinancing, cost reduction, restructuring, efficiency programme, simplification, transformation, footprint reduction, site closure, capacity reduction, redundancy, workforce reduction, capex growth, new facility, capacity expansion, major investment, skills investment, recovery language |

Mappings overlap intentionally. The event is one fact with multiple dimension links, not several separately counted facts.

## Jobs features

| Existing feature family | Count | Mapping |
|---|---:|---|
| open count, count change, vacancy velocity, new and closed vacancies | 5 | Workforce & Capability |
| function count/change/share for operations, procurement, transformation, finance, AI/data and manufacturing | 18 | Workforce & Capability, with contextual links to Delivery/Change only after factual classification |
| geographic hiring expansion | 1 | Workforce & Capability; candidate Demand/Delivery relationship |

## Gaps and cautions

- The existing taxonomy has little explicit coverage of quality, defects, recalls and customer-service performance.
- “Growth language” and “recovery language” are linguistic proxies, not objective demand observations.
- Mentions can be duplicated across narrative and tables; count intensity is not automatically operational intensity.
- Jobs change features require reliable repeated snapshots; the current baseline is not sufficient for lifecycle interpretation.
- EBITDA, profit, gross margin, cash, leverage, working capital and intervention observations exist in extraction but do not all have longitudinal feature definitions.
- Outcome names referenced by candidate signals are research hypotheses, not labels already available to the model.


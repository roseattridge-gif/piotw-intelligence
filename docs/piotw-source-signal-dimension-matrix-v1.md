# PIOTW Source → Signal → Dimension Matrix v1

> **CANDIDATE PRODUCT ONTOLOGY — NOT YET EMPIRICALLY VALIDATED**

| Source | Boundary | Raw evidence | Factual observation/event | Candidate signal | Dimension(s) | Cadence | Backfill | MVP |
|---|---|---|---|---|---|---|---|---|
| Annual/interim reports | issuer | filed report and tables | revenue, margins, cash, debt, capex, intervention events | YoY change, bps change, novelty, persistence | all except some customer-quality cases | event-driven | strong | existing core |
| Results/regulatory announcements | issuer | dated announcement | current financials, guidance, operational actions | current-period change and new-event flags | demand, cost, cash, delivery, change | event-driven | strong | existing/extend |
| Investor presentations | issuer | presentation pages | volumes, backlog, capacity, programme milestones | change and milestone novelty | demand, delivery, change | event-driven | partial | next |
| Company newsroom | issuer | press release | investment, facility, leadership, contract announcement | new event, persistence | delivery, workforce, change | daily | partial | next |
| Company careers/ATS | outside-in | job page snapshots | posting ID, function, seniority, location, status | open count, velocity, function mix, geographic novelty | workforce; sometimes delivery/change | every 2 days | weak | build now |
| Find a Tender / Contracts Finder | outside-in | award and notice records | award, value, buyer/supplier, status | wins/losses, value change, buyer/supplier activity | demand, delivery | daily | strong | build now |
| Product/safety regulators | outside-in | recall/enforcement notice | affected product/site, action, severity | new intervention, recurrence, persistence | quality/customer, delivery, change | daily | strong | build now |
| Environmental/operating regulators | outside-in | enforcement/restriction notice | site restriction, breach, recovery | disruption novelty and duration | delivery, quality/customer, change | daily | strong | build now |
| Planning/permit records | outside-in | application and decision | site, use, floor area, decision, stage | capacity/footprint novelty and progress | delivery, change | weekly | partial | next |
| Site opening/closure notices | mixed | dated public notice | location, function, opening/closure status | footprint change, persistence | delivery, workforce, change | weekly/event | partial | next |

The matrix states what could be observed; it does not say that a source or signal predicts an outcome. Source-specific definitions, cadence and access risks are authoritative in `config/piotw_source_registry_v1.yaml`.

## Source-family feasibility register

| Source family | Update frequency / cadence | Historical backfill / point-in-time | Cost | Legal/access risk | Difficulty | Latency | Commercial relevance | Candidate outcomes | MVP / support |
|---|---|---|---|---|---|---|---|---|---|
| issuer disclosures | event-driven / event-driven | strong / strong | low | low | medium | publication | high | restructuring, warnings, margin change, sites, investment | existing / reports implemented |
| careers/ATS | daily / 2 days | weak / weak without owned snapshots | low | medium | medium | 1–3 days | high | workforce, leadership, capacity, geography | now / one baseline |
| contracts/procurement | daily / daily | strong / strong | low | low | medium | 1–7 days | high | capacity, investment, demand-related future research | now / not built |
| regulatory operating notices | daily / daily | strong / strong | low | low | medium | 1 day | high | disruption, closure, warning, intervention | now / not built |
| physical footprint/capacity | weekly-monthly / weekly | partial / partial | medium | low | high | 1–4 weeks | medium-high | closure, capacity, geography, investment | next / not built |
| company newsrooms | irregular / daily | partial / partial | low | low | low | 1 day | medium | investment, capacity, leadership | next / contract only |

The machine registry additionally supplies source examples, observable facts and exact enumerated cadence units. “Candidate outcomes” are hypotheses to structure later research, not claims of predictive usefulness.

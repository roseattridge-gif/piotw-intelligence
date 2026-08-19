# Evidence Engine 0.3.6 event-family contracts

Status: development-complete; contaminated and synthetic evidence only; not scientifically validated.

## Shared envelope

Every candidate retains immutable evidence text and exact provenance. Before family adjudication, the shared envelope checks that evidence exists, the subject resolves to the issuer/group/segment/subsidiary, and the span is not negated, purely hypothetical or purely historical. These are safety exclusions, not a generic event-sufficiency rule.

Each family then decides whether its own event identity, direction, scope and factual support are present. Unknown types return `AMBIGUOUS / family_not_implemented`.

| Family | Valid identity | Polarity | Minimum direct support | Important exclusions |
|---|---|---|---|---|
| Restructuring / Cost Action | Issuer intervention or indirect cost-base action | Action versus cost increase | Action verb plus intervention identity, or explicit cost-base/workforce/site action | Product/programme name, accounting-only provision, customer/supplier action, ordinary efficiency wording |
| Workforce & Capability | Hiring, workforce reduction, redundancy, labour constraint, skills investment | Expansion, contraction, constraint | Issuer workforce action or condition | Industry labour commentary, third parties, biography, hypothetical staffing risk |
| Delivery & Capacity / Sites | Closure/opening, capacity expansion/reduction/mismatch, actual disruption | Expansion, reduction, disruption | Physical asset/capacity/delivery object plus direction/action | Industry statistics, competitor site, generic risk |
| Demand & Growth | Revenue, sales, order, backlog, demand or volume movement | Increase or decline | Demand-side object plus observed direction | Cost/expense growth, strategy/aspiration, unrelated market statement |
| Supply Chain & Resilience | Actual constraint, inflation pressure or destocking affecting issuer | Constraint or recovery | Named condition plus direct operational effect | Generic supply risk, supplier-only event without issuer impact |
| Quality & Customer / Regulatory | Actual defect/quality event, recall or regulatory action | Adverse or remediation | Issuer event and action/effect | Compliance boilerplate, hypothetical recall, third-party product |
| Change & Execution / Leadership | Active transformation or issuer leadership transition | Change | Launch/implementation/ongoing status or appointment/departure | Director biography, prior employer, generic transformation ambition |

Planned events can be accepted only when the issuer has committed to a specific action; possibility and risk language are rejected. Every accepted result returns the exact candidate source span.

The machine-readable contract is `config/evidence/event_family_contracts_v0_3_6.json`.


# Evidence Engine 0.3.6 development results

## Boundary

All figures below are from the already-contaminated 0.3.5 diagnostic labels. They are engineering regressions, not fresh validation or accuracy estimates. No outcomes or new scientific corpus were accessed.

## Family results

| Family | Cases | Supported accepted | Unsupported rejected | False accepts | Missed supported |
|---|---:|---:|---:|---:|---:|
| Demand & Growth | 86 | 73 | 11 | 2 | 0 |
| Restructuring / Cost Action | 32 | 12 | 14 | 0 | 6 |
| Supply Chain & Resilience | 16 | 6 | 4 | 2 | 4 |
| Workforce & Capability | 8 | 1 | 5 | 1 | 1 |
| Change & Execution / Leadership | 6 | 4 | 0 | 0 | 2 |
| Delivery & Capacity / Sites | 2 | 0 | 0 | 0 | 2 |
| Quality & Customer / Regulatory | 0 | 0 | 0 | 0 | 0 |
| **Total routed** | **150** | **96** | **34** | **5** | **15** |

The restructuring contract improved from ten to 12 supported accepts and reduced missed supported cases from eight to six while retaining zero false accepts on its contaminated subset. It now recognises some indirect cost-base actions while rejecting cost increases, name-only references, third-party actions and accounting-only descriptions.

## Remaining failure classes

- indirect and highly variable intervention language, especially restructuring and simplification;
- supply-chain evidence that mixes issuer impact with supplier/industry context;
- workforce language without a clear grammatical subject;
- sparse contaminated coverage for capacity/sites and no diagnostic coverage for quality/regulatory;
- contextual evidence split across sentence/table boundaries;
- semantic ambiguity that deterministic patterns should leave unresolved rather than force.

## Development decision

The architecture is structurally complete across seven families and has 24 synthetic/contract tests, but it is **not yet ready for a fresh preregistered gate**. First expand development coverage for Delivery/Capacity, Quality/Regulatory, Supply Chain and indirect restructuring language, then freeze a fresh protocol. Official Model 2 readiness remains `NOT READY`.

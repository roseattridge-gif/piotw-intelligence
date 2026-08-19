# Evidence Engine 0.3.6 final development hardening

## What changed

The final pass addressed general failure classes rather than company-specific text:

- stricter hypothetical and historical exclusions;
- observed-change requirements for demand/backlog language;
- active-plan versus accounting-definition handling for restructuring;
- indirect restructuring, site-closure and workforce-reduction meaning;
- realised issuer supply impact, mitigation and persistence;
- continuing multi-year transformation execution;
- broader but polarity-safe facility, line and distribution-centre language.

No issuer identity or report-specific answer is embedded in extraction logic.

## Development evidence

The original 69-case pack is preserved. A second 54-case final-hardening pack adds positive, negative, ambiguous, attribution, temporal, polarity, sparse-context and cross-family adversaries. Combined development coverage is 123 cases, all matching their declared outcomes with exact immutable evidence spans.

The preserved 150-case contaminated diagnostic now produces:

| Family | Supported accepts | Correct rejects | False accepts | Misses |
|---|---:|---:|---:|---:|
| Supply Chain / Resilience | 10 | 6 | 0 | 0 |
| Workforce | 2 | 6 | 0 | 0 |
| Restructuring / Cost Action | 18 | 14 | 0 | 0 |
| Change / Leadership | 6 | 0 | 0 | 0 |
| Demand / Growth | 73 | 13 | 0 | 0 |
| Delivery / Capacity / Sites | 2 | 0 | 0 | 0 |
| Quality / Regulatory | 0 | 0 | 0 | 0 |
| **Total** | **111** | **39** | **0** | **0** |

Quality had no contaminated examples; its readiness rests on 12 synthetic/adversarial cases. Delivery had only two contaminated positives, so its larger 22-case development coverage is particularly important but remains synthetic.

## Cross-family behaviour

Six paired spans test site closure/restructuring, procurement/cost reduction, hiring/capacity expansion, leadership/transformation, supply disruption/cost growth and investment/capacity. The same immutable observation may support two genuinely distinct atomic events. It is not copied into multiple facts merely to populate dimensions, and unsupported remaps remain ambiguous or rejected.

## Boundary

This is the end of development hardening. It is not scientific validation. The fresh corpus remains empty and the gate was not run.


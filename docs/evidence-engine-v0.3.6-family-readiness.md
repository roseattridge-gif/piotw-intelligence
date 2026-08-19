# Evidence Engine 0.3.6 family readiness

This is a development-readiness decision, not an accuracy claim.

READY means positive, negative and ambiguous coverage exists; attribution, polarity, temporal and cross-family adversaries are exercised where applicable; provenance is complete; all known contaminated defects have a general treatment and regression test; and no known architectural defect remains.

| Family | Status | Development basis | Residual risk for fresh gate |
|---|---|---|---|
| Quality / Regulatory | `READY_FOR_FRESH_VALIDATION` | 12 synthetic cases; no known defect | No contaminated real-document examples |
| Delivery / Capacity / Sites | `READY_FOR_FRESH_VALIDATION` | 22 synthetic cases; 2/2 contaminated supported accepts | Sparse contaminated coverage |
| Supply Chain / Resilience | `READY_FOR_FRESH_VALIDATION` | 21 synthetic cases; 10 accepts and 6 rejects on contaminated set | Attribution/context remains the main unseen risk |
| Restructuring / Cost Action | `READY_FOR_FRESH_VALIDATION` | 24 synthetic cases; 18 accepts and 14 rejects on contaminated set | Active-plan accounting context needs unseen challenge |
| Demand / Growth | `READY_FOR_FRESH_VALIDATION` | 14 synthetic cases; 73 accepts and 13 rejects on contaminated set | Revenue versus operational demand semantics |
| Workforce | `READY_FOR_FRESH_VALIDATION` | 14 synthetic cases; 2 accepts and 6 rejects on contaminated set | Limited positive contaminated examples |
| Change / Leadership | `READY_FOR_FRESH_VALIDATION` | 16 synthetic cases; 6/6 contaminated supported accepts | Routine governance versus intervention |

All seven families are ready to spend one preregistered fresh validation set. This does not mean the engine is technically validated or ready for Model 2.


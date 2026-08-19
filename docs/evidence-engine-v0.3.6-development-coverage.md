# Evidence Engine 0.3.6 development coverage

Status: development-only. Synthetic and previously contaminated diagnostics are not scientific validation.

## Expanded cases

The versioned development pack contains 69 synthetic/adversarial cases:

| Family | Cases | Supported accepts | Correct rejects | Correct ambiguous | Synthetic false accepts | Synthetic misses |
|---|---:|---:|---:|---:|---:|---:|
| Delivery / Capacity / Sites | 12 | 7 | 4 | 1 | 0 | 0 |
| Quality / Regulatory | 12 | 8 | 3 | 1 | 0 | 0 |
| Supply Chain / Resilience | 12 | 8 | 3 | 1 | 0 | 0 |
| Restructuring / Cost Action | 14 | 7 | 6 | 1 | 0 | 0 |
| Demand / Growth | 6 | 1 | 4 | 1 | 0 | 0 |
| Workforce | 6 | 2 | 3 | 1 | 0 | 0 |
| Change / Leadership | 7 | 2 | 4 | 1 | 0 | 0 |

Provenance transport was complete for 69/69 cases. No attribution adversary was accepted. No synthetic severe failure occurred.

Coverage includes actual, planned, hypothetical and historical language; target versus third-party attribution; polarity; headings; accounting-only references; fragments; routine disclosures; facility/capacity movements; supply conditions and resilience actions; and quality/regulatory events.

## Preserved contaminated diagnostics

The original 150 routed contaminated cases remain authoritative as known development defects: five false accepts and 15 missed supported events. They are not overwritten by a clean synthetic pack.

| Family | Preserved false accepts | Preserved misses |
|---|---:|---:|
| Demand / Growth | 2 | 0 |
| Restructuring / Cost | 0 | 6 |
| Supply Chain | 2 | 4 |
| Workforce | 1 | 1 |
| Change / Leadership | 0 | 2 |
| Delivery / Capacity | 0 | 2 |
| Quality / Regulatory | 0 | 0 |

The machine-readable assessment is `data/derived/evidence_engine_v0_3_6_development_coverage.json`.


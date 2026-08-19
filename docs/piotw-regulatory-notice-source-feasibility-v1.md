# PIOTW Regulatory Operating Notice Feasibility v1

Status: feasibility only; no regulatory adapter implemented.

## Candidate UK sources

| Source | Observations | History / timestamp | Access | Coverage caveat | Rank |
|---|---|---|---|---|---:|
| OPSS Product Safety Alerts, Reports and Recalls | recall/report/alert, risk, product, corrective measure, date | strong searchable dated archive | public pages/feed | product/manufacturer/entity matching varies | 1 |
| MHRA medicines and medical-device alerts | device/drug alerts and field-safety notices | strong dated archive/feed | public | sector-specific | 2 |
| HSE enforcement notices/public registers | safety enforcement and affected dutyholder/site | strong where register exposes history | public search/export varies | identity and site resolution | 3 |
| Environment Agency public registers/data | environmental permits/enforcement/operating restrictions | partial-to-strong by dataset | multiple public services/APIs | fragmented regimes and entity IDs | 4 |
| DVSA recalls | vehicle recall campaigns | useful dated data, but manufacturer API requires onboarding credentials | authenticated | automotive-only and access constrained | 5 |

## Recommendation

Start with the OPSS public alert/report/recall archive at a daily cadence. It is materially easier than fragmented environmental/enforcement registers, has explicit dates and intervention types, and maps to Quality & Customer, Delivery & Capacity and Change & Execution. Before implementation, verify feed pagination, correction/version behaviour and manufacturer-name resolution against a small corpus.

Regulatory events must remain factual records. A recall is not automatically distress, and differing regulator/sector exposure must remain visible in later benchmarking.


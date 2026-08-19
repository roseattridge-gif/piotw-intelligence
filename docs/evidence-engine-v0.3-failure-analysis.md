# Evidence Engine 0.3 - failure analysis

| Rank | Problem | Frequency | Severity | Model risk | Disposition |
|---:|---|---|---|---|---|
| 1 | No independently frozen human gold yet | universal | critical | accuracy claims invalid | fix before Model 2 |
| 2 | No timed human-first versus assisted review | universal | critical | product economics unknown | fix before Model 2 |
| 3 | Visual-table extraction remains unscored | unknown | high | wrong metric/value/basis | fix before Model 2 |
| 4 | Strategic adjusted metrics have no independent denominators | unknown | high | distorted longitudinal features | fix before Model 2 |
| 5 | Jobs lifecycle lacks elapsed snapshots | universal | high | false closures and unstable counts | fix before Model 2 |
| 6 | Table parser relies on header proximity and issuer wording | report-dependent | high | period/scale ambiguity | tolerate only with review |
| 7 | Event taxonomy mapping can lose reviewer nuance | event-dependent | medium | taxonomy confusion | tolerate with review |

The dominant risk is methodological, not compute: without independent annotation, improving extraction and then grading it against its own output would repeat the 0.2 weakness.

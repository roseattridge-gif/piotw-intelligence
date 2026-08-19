# Evidence Engine 0.3.4 development QA

## Benchmark

The frozen development benchmark contains 230 rows drawn from the six-document diagnostic, the 78-case 0.3.1 benchmark, 0.3.2 table/historical cases, the previous unseen sample, the five-document QA set, 0.3.3 entity/risk cases, and GM/Honeywell/HP failures. Hash: `74d2bccbc4624af5e8db6387c85b0f1c243aa4a68b36aa4392963943d61f65d6`.

The six-document AI diagnostic remained clean: 14 event agreements, zero missed AI events, zero likely false positives, zero duplicates, and zero severe disagreements. There were 84 PIOTW-only candidates classified as possible reviewer omissions and one source-pack ambiguity; these are not accuracy claims.

On the previous 0.3.2 unseen labels, false positives retained fell from 12 to zero and 15 of 17 supported examples remained (88.2% supported retention). On GM/Honeywell/HP, all 13 supported examples remained, false positives fell from 11 to four, and three labelled ambiguities remained. Precision among the retained supported/false-positive rows improved from 43.3% to 76.5%; this still falls below the 85% target and illustrates why a real semantic model run is required.

## Brand-new unseen diagnostic

Three development-safe companies (Intel, 3M, and Microsoft), nine previously unused documents:

| Measure | Result |
|---|---:|
| Deterministic candidates | 459 |
| Deterministic rejects before semantic routing | 158 |
| Semantic-development calls | 186 |
| Accepted events | 182 |
| Semantic rejects | 4 |
| Accepted events inspected | 30 |
| Supported | 29 |
| False positives | 1 |
| Severe false positives | 0 |
| Diagnostic precision | 96.7% |
| Exact support-span provenance | 100% |

The remaining false positive treated conditional wording about revenue growth returning after economic conditions improve as a factual planned growth event. This is the dominant remaining semantic failure class in this sample.

These numbers do not establish model-backed performance. The actual model-call count was zero, so the predeclared gate fails despite the diagnostic result. Status: `NOT TECHNICALLY READY`. Official readiness: `NOT READY`.

# Evidence Engine 0.3.6 fresh-gate readiness

Status: `EVIDENCE_ENGINE_0_3_6_READY_FOR_FRESH_GATE_AUTHORISATION`

The engine is ready for the founder to authorise construction and one execution of the preregistered fresh corpus. No corpus was constructed and no gate was run in this task.

## Frozen package

- Protocol: `config/evidence/fresh_validation_protocol_v0_3_6.json`
- Candidate manifest: `data/evidence_engine_v0_3_6/fresh_candidate_manifest.csv` (headers only)
- Contamination guard: `scripts/check_evidence_v036_contamination.py`
- Family contracts: `config/evidence/event_family_contracts_v0_3_6.json`
- Known-failure register: `data/derived/evidence_engine_v0_3_6_known_failure_register.csv`
- Development results: `data/derived/evidence_engine_v0_3_6_development_coverage.json`

## Corpus requirements

- 7–14 entirely unused companies;
- 14–28 entirely unused documents;
- no overlap by company, ticker, document ID, URL or source hash with any 0.3.x development, blinded-review or AI-review material;
- at least 12 supported, 12 difficult-negative and six ambiguous opportunities per family;
- required attribution, temporal, polarity, hypothetical, historical, fragment, heading-only and accounting-only traps;
- source-first labels frozen before provider execution.

## Frozen thresholds

| Measure | Requirement |
|---|---:|
| Accepted-event precision | at least 90% |
| Supported-event retention | at least 80% |
| Severe false positives | 0 |
| Attribution errors | 0 |
| Provenance completeness | 100% |
| Provider/schema/contract completeness | at least 99% |

The gate runs once, stops on failure and permits no tuning after inspection. Passing it would establish technical semantic readiness only; official Model 2 readiness remains `NOT READY` pending later cross-review/readiness work.


# Evidence Engine 0.3.5 fresh corpus

Status: frozen before semantic execution on 18 August 2026.

The corpus contains 10 official SEC filings from five companies unused in every repository 0.3.x corpus, benchmark, inspection, reviewer pack and diagnostic dataset: PepsiCo, RTX, Cisco, Lockheed Martin and Nike. Each company contributes one annual report and one interim filing. The documents deliberately contain tables, legal/accounting material, historical references, conditional language, third-party references, operational changes and ordinary reporting.

Membership was checked by normalized company name, ticker, source URL and SHA-256 against the prior 0.3.x CSV registries. All 40 checks passed. The manifest is `data/evidence_engine_v0_3_5/fresh_corpus_manifest.csv`; source and candidate membership are frozen in `fresh_source_candidate_freeze.json`.

Deterministic extraction yielded 156 candidates. A source-first review labelled all 156 before any 0.3.5 execution. It is correctly designated `AI_ASSISTED_FINOPS_REVIEW`, `formal_independent_human_gold=false` and `admissible_for_model2_gate=false`. This is a fresh technical generalisation test, not formal independent-human validation.

Frozen hashes:

- corpus manifest: `b31ea6ea192c4f6ebf2a0b98b51713f17bb5bcdf9ef9902afc8d23d1a680e7b9`
- candidate manifest: `a98cf3d827a9b5931eba15b718f8fe716b13a229a30e8e5b65ddadf33dda3bc4`
- label file: `4f1f51286a5ca5b3b7dd0cb28fb9d4d61e057e1c7a8d301a44ce140acc87d346`
- annotation schema: `76e891265501e09e200b469c8994f535772698b02936ae4485bd9449e207286f`

No restructuring or holdout outcomes were used for selection or annotation.


# Evidence Engine 0.3.3 development QA

All results are development diagnostics, not independent validation. Any OpenAI review remains `AI_ASSISTED_FINOPS_REVIEW` with `formal_independent_human_gold=false`.

## Protected regressions

- Six-document comparison: 14 agreements, zero missed reviewed events, zero diagnosed false positives, zero duplicates and zero severe disagreements.
- Five-document historical/table QA: all 28 supported accepted events retained; zero retained false positives.
- Prior 0.3.2 unseen set: accepted events fell from 64 to 46. Of the thirty previously inspected rows, 15 supported examples remained and all twelve false positives were removed. Two supported examples were suppressed.

## New unseen sample

The frozen implementation was evaluated on GM, Honeywell and HP: nine previously unused documents, 363 candidates and 129 accepted events. Thirty accepted events were inspected.

| Classification | Count |
|---|---:|
| Supported | 13 |
| Obvious false positives | 11 |
| Ambiguous | 6 |
| Severe false positives | 2 |

Development diagnostic precision was 43.3%, below the predeclared 85% threshold. One attribution error remained. Dominant failures were wrong/legal context, hypothetical risk, malformed fragments, cross-references, industry context and taxonomy mismatch.

## Decision

`NOT TECHNICALLY READY FOR HUMAN REVIEW`.

The next dominant problem is semantic entailment: proving that the exact span supports the precise taxonomy event, not merely that the span concerns the issuer. The extractor is not frozen and the formal blinded study should not start against this version.

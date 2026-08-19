# Evidence Engine 0.3.2 historical/table hardening

## Scope and boundary

This phase addresses historical accounting disclosures, comparative tables and malformed PDF fragments. It does not use restructuring outcomes, alter the frozen model, train Model 2, or change the independent-human readiness gate.

The dedicated frozen benchmark contains all 19 obvious 0.3.1 fresh-sample false positives, the five ambiguous cases, and eleven generalized cases. It has 35 development-only rows and SHA-256 `82f38aba44f85e4a496b9ca0060e9c1e5ec60e48385b699f5686e0804b919722`.

## Root causes addressed

- historical or comparative restructuring-cost tables;
- accounting measures incorrectly promoted to operational interventions;
- table footnotes and reconciliation rows;
- repeated/misaligned headings and page contamination;
- multi-year and mixed-period binding;
- completed or previously announced programmes;
- technical/accounting uses of restructuring terminology.

The key data-model change is explicit separation between `accounting_observations` and accepted operational events. Rejected operational promotion does not discard the underlying financial fact.

## Remaining weakness

The second unseen sample exposed third-party attribution, generic risk language and non-table contextual uses that were not the target of this phase. Those failures prevent a technical freeze even though the historical/table regression itself improved materially.

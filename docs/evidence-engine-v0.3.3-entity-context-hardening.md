# Evidence Engine 0.3.3 entity/risk-context hardening

This phase adds explicit subject attribution over the 0.3.2 table-aware pipeline. It preserves candidate/context/final-event separation, table-period controls, accounting-observation separation and provenance.

The frozen 29-case development benchmark contains the twelve 0.3.2 unseen false positives, its ambiguous case and sixteen generalized subject/risk examples. It is development-only, `formal_gold=false`, and inadmissible for the Model 2 gate.

Implemented controls cover supplier, customer, competitor, industry, quotation, biography, acquisition-target, joint-venture, subsidiary and segment subjects; generic versus factual risk; modal sentences with embedded facts; technical redundancy; accounting cross-references; and page/table joins.

The previous unseen sample improved from 12 retained false positives to zero among the previously inspected rows, while retaining 15 of 17 supported rows. However, the next genuinely unseen GM/Honeywell/HP sample exposed semantic taxonomy mismatches, cross-references, malformed joins and hypothetical statements. These failures show that target-company attribution alone is insufficient when the asserted event meaning is wrong.

No issuer-specific extraction exception was introduced. No restructuring outcome was accessed.

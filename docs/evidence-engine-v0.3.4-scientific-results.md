# Evidence Engine 0.3.4 scientific semantic-quality results

Execution: `SCIENTIFIC_SEMANTIC_GATE_RERUN_AFTER_MECHANICAL_CONTRACT_REPAIR`

Batch: `batch_6a832dbf3d2c81909c2ff50f828be0da`

## Contract reliability

- Provider completion: 685/685 (100%)
- Strict-schema-valid output: 685/685 (100%)
- Locally contract-valid output: 685/685 (100%)
- Accepted decisions resolving to exact immutable evidence: 603/603 (100%)
- Provider failures: 0
- Invalid decisions: 0
- Unknown pointers: 0
- Truncations: 0

The output set is sufficiently complete for semantic interpretation under the frozen methodology.

## Frozen semantic-quality results

| Evaluation set | Precision | Supported-event retention | False positives | Severe false positives | Attribution errors | Provenance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Prior unseen | 100% | 88.24% (15/17) | 0 inspected false positives | 0 | 0 | 100% |
| GM / Honeywell / HP | 59.09% | 100% (13/13) | 9 inspected false positives | 1 | 1 | 100% |
| Mandatory brand-new unseen | 96.67% | 100% (29/29) | 1 | 0 | 0 | 100% |

The general benchmark retained 72/80 supported events (90%). The six-document AI diagnostic retained two PIOTW-missed events, zero likely false positives and zero duplicates. These diagnostic annotations remain non-formal and inadmissible for Model 2 readiness.

## Usage and decision

- Input tokens: 717,125
- Output tokens: 511,301
- Reasoning tokens: 402,112
- Total billed input plus output tokens: 1,228,426
- Actual Batch cost: USD 0.600941625

Semantic gate: **FAIL**.

The GM/Honeywell/HP mandatory subset failed the frozen precision threshold and contained one severe false positive and one attribution error. The six-document diagnostic also retained two missed AI-reviewed events. The result is therefore `NOT TECHNICALLY READY`.

No tuning was performed. Evidence Engine 0.3.4 remains unfrozen and no cross-review pack was created. Official Model 2 readiness remains `NOT READY`. The preserved prior Batch remains a provider/contract execution failure and is not reinterpreted here.

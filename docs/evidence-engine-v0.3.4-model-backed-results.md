# Evidence Engine 0.3.4 model-backed results

The authorised provider was invoked, but no request produced a valid structured semantic decision. Precision is therefore not measurable. This is preserved as `MODEL_PROVIDER_EXECUTION_FAILURE`, not a semantic-quality result.

| Evaluation | Accepted | Ambiguous | Live precision | Supported retention |
|---|---:|---:|---:|---:|
| 230-case semantic benchmark | 0 | 230 | Not measurable | 0/80 |
| Previous unseen | 0 | 46 | Not measurable | 0/17 |
| GM/Honeywell/HP | 0 | 129 | Not measurable | 0/13 |
| Brand-new unseen | 0 | 186 | Not measurable | 0/29 |

The six-document diagnostic consequently recorded 14 missed reviewed events and one source ambiguity. There were no accepted false positives, severe false positives, or attribution errors because nothing was accepted; this is not evidence of precision. Accepted-event provenance is not measurable.

Scientific gate result: not measured because provider preflight was not functional. Dominant failure: `MODEL_PROVIDER_EXECUTION_FAILURE`. Extractor frozen: no. Cross-review pack created: no. Official Model 2 readiness: `NOT READY`.

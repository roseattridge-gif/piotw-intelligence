# Evidence Engine 0.3.4 extractor freeze decision

Decision: **DO NOT FREEZE**.

Model-backed execution follow-up: `MODEL_BACKED_VERIFICATION_BLOCKED_NO_CREDENTIAL`. No authorised provider request ran, so the mandatory live gate remains unevaluated and the extractor remains unfrozen.

First authorised follow-up run: 646 requests were attempted, but all failed closed (596 HTTP errors and 50 response-shape/index errors). No valid structured semantic decision was produced. The gate failed with dominant class `MODEL_PROVIDER_EXECUTION_FAILURE`; the extractor remains unfrozen. No second attempt or tuning was performed.

The predeclared gate requires a model-backed unseen evaluation. No authorised model credential was available, and the development run used `deterministic_semantic_development / semantic-rules-v0.3.4`. Although the unseen diagnostic produced 29 supported events out of 30 inspected with no severe false positive, it cannot demonstrate the real semantic provider's structured-output reliability, accuracy, latency, tokens, or cost.

The code, prompt, configuration, taxonomy, benchmark, and results are versioned and hashable, but they are not designated as a frozen extraction release. No blinded cross-review pack was created because the gate did not pass. Official Evidence Engine readiness remains `NOT READY`.

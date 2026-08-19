# Evidence Engine 0.3.4 model-backed run

Status: `NOT TECHNICALLY READY`

The first authorised gate run executed once on 16 August 2026 using the frozen OpenAI Responses API configuration and `gpt-5-mini`.

Configuration remained unchanged: prompt `semantic-event-v0.3.4`, schema `semantic-schema-v0.3.4`, maximum output 500 tokens, no temperature parameter, bounded evidence context, existing taxonomy/rules/samples, and fail-closed handling. No outcomes, predictions, reviewer answers, or future evidence were sent.

## Execution result

- Requests attempted: 646
- Successful structured decisions: 0
- HTTP errors: 596
- Response-shape/index errors: 50
- Fail-closed ambiguous decisions: 646
- Reported input/output tokens: 0 / 0
- Recorded API cost: $0.00
- Average attempted-call latency: 912 ms

The dominant failure is `MODEL_PROVIDER_EXECUTION_FAILURE`, not measured semantic classification quality. Every failed call correctly became ambiguous; there was no deterministic fallback. The first authorised run is preserved and will not be rerun or tuned in this phase. The extractor remains unfrozen and official Model 2 readiness remains `NOT READY`.

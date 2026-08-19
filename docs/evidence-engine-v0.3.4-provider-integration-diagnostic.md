# Evidence Engine 0.3.4 provider-integration diagnostic

## Conclusion

The first 646-call attempt is preserved as `MODEL_PROVIDER_EXECUTION_FAILURE`. It did not measure semantic quality.

Two independent provider defects explain the zero usable decisions:

1. The project had no OpenAI SDK installed and used a hand-written response parser that assumed `output[0].content[0].text`. Fifty HTTP-success responses reached that invalid shape assumption and raised `IndexError`. The integration now uses the official SDK's `response.output_text` helper.
2. Those first 50 attempts consumed the API project's 50 requests-per-day allowance. The next 596 attempts were recorded only as `HTTPError` because the original audit discarded HTTP status and provider error bodies. A new synthetic request reached OpenAI and returned HTTP 429, code `rate_limit_exceeded`, explicitly reporting RPD limit 50, used 50.

The original logs cannot retrospectively prove the HTTP status of each of the 596 failures. They must remain classified as status unavailable rather than silently relabelled as 429, although the contemporaneous smoke test and sequence strongly support daily-limit exhaustion as the operational explanation.

## Safe root-cause table

| Population | Status | Count | Safe error evidence | Finding |
|---|---:|---:|---|---|
| First attempt, HTTP errors | Not captured | 596 | Original audit retained only `HTTPError` | Status distribution cannot be reconstructed |
| First attempt, HTTP-success shape errors | 2xx | 50 | `IndexError` at fixed nested-output assumption | Responses API output shape parsed incorrectly |
| Synthetic Smoke Test A | 429 | 1 | `rate_limit_exceeded`, requests/day limit 50, used 50 | Authentication/model endpoint reached; daily request allowance exhausted |

## SDK and integration repair

- SDK before: not installed.
- SDK after: official `openai==3.1.0`, pinned in `pyproject.toml`.
- Request: Responses API with structured output under `text.format` and `type=json_schema`.
- Parsing: `response.output_text`, followed by JSON and existing semantic-schema validation.
- Error audit: status, provider type/code/param/message, retry count, response status, usage and latency; authorization headers and credentials are excluded.
- Retry: bounded exponential backoff only for short-lived 429/500/502/503, connection errors and timeouts. Requests-per-day exhaustion is not retried.

The official OpenAI model reference confirms that `gpt-5-mini` supports the Responses endpoint and Structured Outputs.

## Synthetic preflight

| Test | Result | Detail |
|---|---|---|
| A — minimal unstructured Responses call | FAIL | HTTP 429 daily request allowance exhausted |
| B — tiny structured output | NOT RUN | A must pass first |
| C — frozen PIOTW schema synthetic accept | NOT RUN | A must pass first |
| C — frozen PIOTW schema synthetic reject | NOT RUN | A must pass first |

`make semantic-provider-preflight` now enforces this order and blocks at the first failure. Unit tests do not make paid requests and cover current SDK response parsing, strict validation, permanent HTTP errors, daily-limit 429, transient retries, incomplete results, cache separation and evidence-span enforcement.

Provider status: `MODEL_PROVIDER_PREFLIGHT_FAILED`.

Gate-rerun status: not technically eligible. The full gate was not rerun. A rerun would also require an API tier whose request allowance can accommodate the unchanged gate; the current 50-RPD allowance cannot support it.

## Scientific integrity

The semantic prompt, schema meaning, model, taxonomy, deterministic rules, samples, labels and readiness gate were not changed. No outcomes were accessed, no Model 2 was trained, and official readiness remains `NOT READY`.

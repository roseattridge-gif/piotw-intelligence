# Evidence Engine 0.3.4 semantic cost analysis

No paid model call was made, so observed API cost and model latency are both unavailable rather than estimated as actuals.

The unseen run routed 186 of 459 candidates (40.5%) to semantic verification across nine reports: 20.7 calls per report. Deterministic filtering avoided 273 potential calls (59.5%).

For planning only, using 600 input and 120 output tokens per call and the published `gpt-5-mini` prices of $0.25 per million input tokens and $2.00 per million output tokens, the estimate is $0.00039 per call, about $0.0081 per report, and about $0.016 per two-report company snapshot. Actual token and latency measurements must replace these assumptions during the authorised model-backed benchmark. [OpenAI model and pricing reference](https://openai.com/index/introducing-gpt-5-for-developers/).

| Scale (two reports/company) | Estimated calls | Estimated semantic cost |
|---|---:|---:|
| 100 companies | 4,133 | $1.61 |
| 1,000 companies | 41,333 | $16.12 |
| 10,000 companies | 413,333 | $161.20 |

Without deterministic pre-filtering, the same candidate volume would be about 10,200 calls per 100 companies and $3.98 at the same token assumptions. These estimates exclude ingestion, storage, retries, and human review.

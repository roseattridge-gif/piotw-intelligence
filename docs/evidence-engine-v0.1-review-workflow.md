# Evidence Engine 0.1 — factual review workflow

## Purpose

Review answers “Is this extracted fact correct?” It does not ask a reviewer to invent a predictive score.

## Queue item

Each review item contains:

```text
Source: Synthetic Annual Report 2024
Location: line 2
Exact evidence: Operating margin: 12.00 percent

Candidate observation
Type: operating_margin
Period: FY2024
Value: 12.00
Unit: percent
Currency: null
Parser: report-regex-0.1.0
Confidence: 0.99

[accept] [correct value/unit] [reject]
```

## Decisions

- **Accept:** candidate becomes eligible for features.
- **Correct:** reviewer supplies corrected value and optionally unit; original span and parser provenance remain attached; status becomes `corrected`.
- **Reject:** candidate remains auditable but is excluded from events and features.

Every decision records reviewer, timestamp, action, optional correction, and note in `ee01_review_decisions`.

## LLM boundary

An LLM may later locate passages or propose mappings. Any such observation must record model, prompt version, timestamp, exact source span, confidence, and validation status. The contract rejects an `llm_assisted` observation without model and prompt provenance.

The 0.1 demo uses deterministic extraction only and makes zero LLM calls. Its synthetic gold review automatically accepts fixture facts solely to test the workflow. It is not a substitute for human review of real reports.

## Review priorities for real reports

Reviewers must check:

- adjusted versus statutory definitions;
- continuing versus discontinued operations;
- group versus segment metrics;
- currency and scale;
- restated comparatives;
- whether prior-period figures use the same definition;
- report publication availability;
- duplicate/boilerplate language;
- whether acquisitions/disposals make comparisons invalid.


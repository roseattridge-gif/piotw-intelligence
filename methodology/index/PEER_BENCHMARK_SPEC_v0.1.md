# PIOTW Peer Benchmark Specification v0.1

**Status:** PROVISIONAL / NOT EMPIRICALLY VALIDATED  
**Methodology version:** 0.1.0

## Benchmark objective

The benchmark makes each eligible feature and dimension interpretable relative to genuinely comparable companies at the same information cutoff. Cohorts must be point-in-time, documented and reproducible. No peer distribution is constructed in v0.1.

Candidate matching fields are sector/industry, business model, revenue scale, market-cap scale, operating geography and listed/unlisted status. Revenue is the preferred initial size measure for operating comparability; market capitalisation is secondary because price changes can move a company between bands without an operational change.

## Ordered cohort selection

1. Preferred: same granular sector and business-model family, broadly comparable revenue, comparable primary geography, and same listing status where available.
2. Broaden the revenue band while retaining sector and business model.
3. Broaden the sector taxonomy one documented level while retaining revenue and geography where possible.
4. Use a broader listed-company benchmark, clearly identified as such.

Every run must store the taxonomy version, filters, inclusions/exclusions, as-of date, cohort `n`, fallback level and transformation method. A company must not benchmark against itself. Survivorship-free historic membership is required for validation.

## Provisional sample-size policy

| Cohort size | Classification | Display rule |
|---:|---|---|
| 50+ | preferred | percentile-like result may be displayed, subject to other quality gates |
| 30–49 | acceptable | display with `n` and cohort disclosure |
| 20–29 | caution | display prominent small-cohort caution |
| below 20 | insufficient | do not display a precise percentile; show contextual comparison only |

These thresholds need empirical validation. Ties, boundary effects, sector skew and cohort churn must be tested. Example disclosure: “23rd percentile vs European Industrial Engineering companies, n=68; cohort method v0.1.0; as of YYYY-MM-DD.”

## Candidate transformations

Percentile ranks, robust z-scores using median/MAD, and empirical cumulative distributions are candidates. Robust transformations are preferred for testing because corporate features are commonly skewed and outlier-prone. Conventional z-scores may be retained as a diagnostic, not the default. The target user-facing mapping is percentile-like 0–100, with 50 approximately the peer median and higher meaning operationally stronger. It is not selected or calibrated in v0.1.

Missing disclosure must not be treated as healthy evidence or silently replaced with the cohort median. Coverage, missingness, confidence and cohort sufficiency must be shown alongside every result.

# PIOTW Benchmark Method v1

Status: architecture only; method not validated and no real percentile is calculated.

## Cohort construction

Peers must match business model before sector label: UK branch-based building-material distributors, specialist merchants and tool/distribution networks. Geography, revenue scale, branch density, customer mix and lease/property intensity must be recorded. A broad industrial or retail cohort is not automatically comparable.

## Comparable windows

Features use the same point-in-time lookback and acquisition cadence. Counts become rates where exposure differs (per 100 branches, per £bn revenue, per 1,000 roles). A company is ranked only when minimum coverage and entity resolution pass.

## Normalisation and missingness

- Winsorise only under a preregistered rule.
- Preserve direction and unit before z-score or percentile conversion.
- Missing is not zero or average.
- Report source coverage, history depth and entity-resolution confidence beside any percentile.
- Never aggregate a dimension when material feature families are systematically missing.

## Percentiles and dimensions

Feature percentiles are empirical ranks within the eligible cohort/window. Dimension aggregation requires preregistered weights or a transparent equal-weight research baseline; neither is authorised here. One canonical observation may link to multiple dimensions without being duplicated.

Any prototype display must say: `ILLUSTRATIVE BENCHMARK — METHOD NOT YET VALIDATED`.


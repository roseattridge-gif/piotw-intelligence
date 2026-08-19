# PIOTW Benchmark Engine v1 Design

> **DESIGN ONLY — NO BENCHMARK SCORE IS IMPLEMENTED OR VALIDATED**

## Purpose

The benchmark engine would place a factual company signal in historical and peer context without turning it into a health score. Example: an operating-margin change of -240 bps may be shown against the company’s own history and a comparable peer distribution.

## Inputs and outputs

Inputs are versioned, cutoff-safe signal snapshots with comparability metadata. Outputs are benchmark snapshots containing peer-set version, population, coverage, percentile or robust deviation, and provenance to every included signal.

## Peer construction

Candidate matching attributes are industry/activity, size, geography, business model and capital intensity. Peer membership must be dated and versioned. A proposed initial rule is at least 20 comparable observations for a displayed percentile; 10–19 may be labelled low coverage; below 10 is suppressed. These thresholds are design candidates and must be frozen before evaluation.

## Measures

- **State:** current level against peers.
- **Change:** period-on-period movement against comparable peer movement.
- **Velocity:** rate of arrivals/closures or repeated operational change.
- **Novelty:** first observed state within available history.
- **Persistence:** consecutive comparable periods or snapshots.
- **Company history:** robust deviation from its own prior distribution.

Use medians, percentiles and median absolute deviation where distributions are skewed. Never replace missing with zero. Report numerator, denominator, coverage period and comparability exclusions.

## Dimension presentation

Dimensions organise benchmark cards; they are not aggregated scores. If later research proposes an index, its construction, weighting and validation must be a separate frozen experiment.

| Dimension | Candidate measures | Directionality | Comparability issue | Percentile meaningful? |
|---|---|---|---|---|
| Demand & Growth | revenue/volume/order/backlog change | contextual; growth usually positive | sector cycles and acquisitions | yes, within comparable activity |
| Delivery & Capacity | utilisation, delays, disruption, footprint change | contextual | asset-light versus asset-heavy | only with business-model peers |
| Cost & Productivity | margin change, cost actions, productivity | higher efficiency usually positive | adjusted/statutory definitions | yes with harmonised basis |
| Cash & Working Capital | conversion, inventory/receivable/debt change | metric-specific | seasonality and financial firms | yes with sector rules |
| Workforce & Capability | vacancy state/velocity/mix, labour events | contextual | company size and ATS coverage | only after coverage normalisation |
| Supply Chain & Resilience | constraints, recovery, inventory context | fewer constraints usually positive | narrative reporting intensity | limited until observation quality improves |
| Quality & Customer | recalls, defects, enforcement, customer conditions | fewer adverse events usually positive | regulator and exposure coverage | event-rate percentile where exposure known |
| Change & Execution | programme novelty, milestones, completion | contextual | programme size and disclosure practice | trajectory/peer rate, not simple level |

## Leakage and reproducibility

At cutoff T, only evidence available by T, peer membership known by T and signals computed under the named feature version may enter. The benchmark snapshot is immutable and reproducible from IDs and hashes. Outcomes never enter peer benchmarking.

# Model card: PIOTW Evidence Model 0.2

## Status

MVP candidate, implemented and integration-tested. The weights are research priors and the model is **not validated for commercial prediction**. The three-company retrospective pilot remains the only outcome test and failed to beat the best simple comparator.

## Intended use

- generate auditable research hypotheses about operational pressure and expansion;
- rank companies for deeper human research once coverage is sufficient;
- test whether public non-financial evidence adds predictive value;
- show exactly which evidence increased or reduced a probability.

Not intended for investment advice, automated decisions about people, credit decisions, or claims of causal inference.

## Outputs

For each company, cutoff and horizon (6, 12 or 18 months):

- operational-pressure probability;
- expansion/transformation probability;
- evidence confidence;
- weighted source coverage;
- itemised positive and negative contributions;
- missing evidence families.

Probability and confidence answer different questions. A 70% probability with 15% confidence means the observed evidence points strongly in one direction but coverage is too thin to rely on it.

## Algorithms

### MVP prior model

A bounded, deterministic weighted-evidence model. Evidence is time-decayed exponentially, duplicates are grouped by event cluster and the result updates an explicit base rate on log-odds scale. No language model chooses the direction or score.

### Feature calculations

- rolling changes and rates;
- functional shares and taxonomy matches;
- persistence/removal time;
- median/MAD company normalisation when enough history exists;
- peer percentiles when sector data exists;
- text/category novelty;
- exponential half-life decay;
- source and event deduplication.

The repository currently implements ATS snapshot deltas and role-family shares. The remaining catalogue entries define the contracts for subsequent deterministic extractors; they are not falsely shown as collected data.

### Candidate statistical models

Regularised logistic/ordinal/linear models may be estimated only after the minimum sample and temporal holdout exist. They must be compared with the weighted model and financial-only baselines. Complex ensembles are out of scope until they demonstrate stable out-of-time value.

## Evidence families and weights

| Family | Pressure | Expansion |
|---|---:|---:|
| Workforce demand and skills | 15% | 22% |
| Operational disclosure | 16% | 10% |
| Leadership and organisation | 12% | 12% |
| Capacity and footprint | 10% | 16% |
| Procurement and contracts | 9% | 12% |
| Product, quality and customer | 12% | 8% |
| Corporate actions | 7% | 6% |
| Web and narrative | 7% | 6% |
| Sector and macro | 7% | 4% |
| Financial state | 5% | 4% |

Full feature definitions and half-lives are machine-readable in `intelligence/ontology/signal_catalog_v02.yaml`. These weights must not be optimised on the three original companies.

## Confidence controls

- no evidence: zero confidence and the prior probability;
- fewer than two independent event clusters: confidence cannot exceed 55%;
- no non-company source: confidence cannot exceed 70%;
- missing source families reduce weighted coverage;
- collector failure is missing data, never a healthy signal;
- repeated versions of the same event share a cluster contribution cap.

## Evaluation criteria

- Brier score;
- calibration by probability band;
- average precision/PR-AUC;
- precision and recall at declared thresholds;
- top-quintile lift;
- median lead time;
- outcome and source coverage;
- family ablations and financial-only comparisons.

## Known limitations

- no free historical company-level jobs archive;
- current pilot has three companies and one retained pre-cutoff disclosure each;
- job taxonomy is deterministic and deliberately simple;
- company pages may be incomplete, dynamic or inaccessible under site policy;
- official company statements are reliable evidence of what was stated, not independent proof that the statement is correct;
- procurement databases capture only covered public contracts;
- causal attribution is not supported.

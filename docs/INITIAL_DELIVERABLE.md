# Initial deliverable — review baseline

## A. Architecture and data flow

Official APIs and permitted company pages → immutable raw document store → parser → facts → deterministic signals → evidence clusters → hypotheses → five scores and predictions → frozen backtest snapshots → outcomes and model comparison → research UI.

PostgreSQL is the system of record. Object storage retains originals. Python owns collection, research, scoring, and backtests. React/TypeScript presents read-only research views as a static Vite application suitable for GitHub Pages. LLM extraction sits behind one provider interface; it may propose structured evidence, never scores. Every derived record carries version identifiers. A failed adapter is logged and isolated.

## B. Build backlog

### Now

1. Phase 0 schema, interfaces, ontology, assumptions, synthetic journey and leakage/scoring tests.
2. Freeze a Companies House/SIC-derived cohort protocol before observing outcomes.
3. Implement three adapters: Companies House, regulated/company reports, ONS.
4. Select three pilot companies from the frozen cohort by deterministic stratified sampling.
5. Manually validate source dates and 50–75 evidence snippets per pilot.

### Next

1. Reach 300–500 manually labelled snippets; measure unsupported-inference rate.
2. Implement hard financial signals, ten conditions, clustering, decay profiles and five baselines.
3. Label objective outcomes blind to predictions; run the 2021 cutoff backtest.
4. Run ablations and calibration analysis; decide Gates 1–4.

### Later

Careers, procurement, narrative enrichment, all five mature scores, 30-company expansion, then buyer tests—each conditional on the prior gate.

### Explicitly not now

Billing, auth/SSO, multi-tenancy, mobile, agents, graph/vector databases, paid datasets, portfolio/CRM workflows, and polished commercial reports.

## C. Database design

The migration is authoritative. Core lineage is `sources → documents → facts → signals → hypothesis_evidence → hypotheses/scores/predictions`; clusters link repeated facts; outcomes are appended independently. Composite uniqueness prevents mutated snapshots. The most important index is `(company_id, available_at)` because every backtest applies its cutoff there. Cost, benchmarks, assumptions, model versions and experiment results are first-class records.

## D. Ontology v0.1

Twenty seeded families: supply constraint, quality deterioration, production constraint, forecasting weakness, working-capital pressure, cost-base inflation, underutilisation, labour constraint, engineering bottleneck, digital debt, transformation drag, customer friction, commercial weakness, procurement weakness, knowledge concentration, leadership instability, acquisition-integration risk, capacity constraint, demand weakness and execution recovery. Full definitions and falsifiers are in `docs/ontology/ONTOLOGY.md`.

## E. Historical research design

Primary cutoff: 31 December 2021. Prediction horizons: 6, 12 and 18 months. Evidence eligibility uses `available_at`, never period end. Publication and availability dates are separately verified; ambiguous availability is conservatively moved later. Cohort and labels are frozen before feature inspection. Predictions are append-only and hashed with version/configuration. Outcome coders do not see model probabilities; extraction validation samples include negative/neutral snippets. Evaluation reports precision, recall, F1, PR-AUC, ROC-AUC where valid, Brier score, calibration, ranking lift, lead time and error rates with company-clustered bootstrap intervals. Compare five specified baselines and pre-registered ablations. With ~30 companies, emphasise uncertainty and repeated company-date observations; do not claim statistical significance from a single small holdout.

## F. Cohort selection

On a stated freeze date, take all London Stock Exchange Main Market and AIM ordinary-equity issuers domiciled in the UK. Join Companies House identity and retain specified industrial/manufacturing/engineering/aerospace/automotive/industrial-technology SIC and ICB subsectors. Require continuous listing and accessible English annual/interim reports across the study window; exclude funds, shells, pre-revenue resource exploration and companies without resolvable identity. Publish the full eligible list and exclusion reasons. Stratify by subsector and log revenue band, then select 30 using a fixed public random seed. Delistings after the sampling freeze remain, preventing survivorship bias. Pilot three are sampled from separate strata, not selected for known outcomes.

## G. Cost estimate (planning ranges, not commitments)

Local Phase 0 costs £0. GitHub Pages and standard GitHub Actions for a public repository can host and build the static interface at no cost within GitHub's current terms. Supabase is not provisioned at Phase 0. API costs are the only likely variable cash cost; the default is **AI disabled**, with a hard daily cap when enabled.

| Scale | Infrastructure | AI extraction planning allowance | Practical expectation |
|---|---:|---:|---|
| 3 companies | £0 | £0–£15 total | Start deterministic/manual; ask before any paid API call |
| 30 companies | £0 if free quotas fit | £25–£150 total | Batch, cache and sample before full processing |
| 100 companies | likely £0–£50/month | £100–£500 total | Re-estimate from measured pilot document/token volumes first |

These are deliberately broad because document counts and token density are unknown. No spend is authorised by this estimate.

## H. Stage gates

1. **Extraction:** ≥90% provenance/date completeness; ≥95% numeric-field accuracy; ≥85% macro-F1 on material fact classes; unsupported inference ≤2%; 100% leakage tests pass.
2. **Inference:** blinded expert agreement κ≥0.60 on condition direction; ≥90% explanations reconstruct exactly; contradictions/alternatives present for ≥90% of material hypotheses.
3. **Predictive signal:** at least one pre-registered operational outcome has PR-AUC ≥1.25× base rate, positive top-quintile lift with 95% clustered-bootstrap interval above 1.0, and median useful lead time ≥90 days.
4. **Incremental alpha:** PIOTW improves PR-AUC ≥10% and Brier score ≥5% versus the best simple baseline, with bootstrap support in ≥80% resamples and no catastrophic subgroup failure.
5. **Trust:** ≥80% of five blinded domain reviewers can correctly explain the score and ≥4/5 rate the evidence chain decision-usable; zero provenance failures.
6. **Willingness to pay:** at least 3 of 10 qualified buyers undertake a consequential pilot or 2 sign paid letters/pilots. No pricing product is built before this test.

Thresholds are decision rules, not guarantees. Gate 4 failure means the work is not described as proprietary intelligence.

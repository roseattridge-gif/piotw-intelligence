# PIOTW Intelligence MVP architecture

## Purpose

The MVP is a research system for one question:

> Do public, outside-in operational signals improve prediction of later company outcomes beyond simple financial baselines?

It is not an investment recommendation system, a share-price model, a web scraper that treats everything online as fact, or a language model that invents a score.

## System boundary

The MVP runs locally at no external service cost. Source collection uses documented public APIs or explicitly configured public pages. Raw/normalised data is stored in local files and SQLite. The React application is a static research dashboard. PostgreSQL remains a deployment-ready schema, not a required dependency. GitHub Pages is the intended publication route only if the owner later authorises publishing.

```text
PUBLIC SOURCES
  company disclosures | ATS job feeds | Companies House | contracts | regulators | ONS
        │
        ▼
SOURCE ADAPTERS
  fetch slowly; record source URL, availability time, retrieval time and hash
        │
        ▼
NORMALISED EVIDENCE
  document → fact/observation → deduplicated event cluster
        │
        ▼
FEATURE ENGINE
  company-relative change | sector-relative change | persistence | novelty | materiality
        │
        ├───────────────┐
        ▼               ▼
PRESSURE MODEL     EXPANSION MODEL
  6/12/18 months     6/12/18 months
        │               │
        └───────┬───────┘
                ▼
PREDICTION + EXPLANATION
  probability, confidence, supporting/contradicting evidence, missing coverage
                │
                ▼
OUTCOME VERIFICATION + WALK-FORWARD BACKTEST
  Brier, calibration, PR-AUC, top-quintile lift, lead time, coverage, baselines
```

## Components

### 1. Source registry and collectors

Each company has stable identifiers: legal name, aliases, company number, ticker, website, careers URL and ATS tenant identifier. Each adapter is responsible only for retrieval and source-specific normalisation. It does not decide whether a fact is positive or negative.

Implemented connectors:

- Greenhouse, Lever, Ashby, SmartRecruiters and Recruitee published vacancies;
- schema.org `JobPosting` extraction for already-authorised page retrieval;
- Companies House company, filing and officer records;
- ONS dataset catalogue/version access;
- Contracts Finder published OCDS notices;
- SEC submissions and company facts.

### 2. Evidence model

An observation contains:

- company, source and evidence-family identifiers;
- event date, public availability date and retrieval date;
- metric, raw value/unit and normalised strength;
- direction for each predictive target;
- source reliability, measurement quality, materiality and independence;
- source URL, content hash and optional event-cluster identifier;
- extraction method/status and an explicit explanation.

Public availability, not reporting-period end, controls eligibility. Missing coverage is stored separately; absence is not converted to healthy evidence.

### 3. Feature engine

The first algorithms are intentionally simple and inspectable:

- `count`, `rate` and functional shares;
- percentage/absolute change over 13, 26 and 52 weeks;
- persistence and time-to-disappearance;
- company-relative robust z-score using median/MAD when history exists;
- sector percentile when a peer benchmark exists;
- novelty against the company’s trailing vocabulary/category history;
- exponential time decay using a feature-specific half-life;
- duplicate-event clustering so copied releases do not multiply evidence.

Job disappearance means “no longer observed,” not “filled.” A source outage produces missing coverage, not mass job closures.

### 4. Predictive models

#### Operational pressure

Target: probability of a defined adverse operational event within 6, 12 or 18 months, including material margin/cash deterioration, profit warning, restructuring, impairment, remediation or inventory correction.

#### Expansion and transformation

Target: probability of previously unannounced capacity investment, transformation programme, sustained hiring growth, material recovery, or product/geographic/manufacturing expansion within 6, 12 or 18 months.

#### Continuous financial outcomes

Evaluated separately: subsequent change in operating margin, cash conversion, sector-relative revenue, inventory days and working capital. The MVP does not convert this into one opaque score.

### 5. Scoring algorithm

For evidence item `i`, model `m` and family `f`:

```text
raw(i,m) =
  family_weight(f,m)
  × strength
  × source_reliability
  × measurement_quality
  × materiality
  × recency
  × independence
  × relevance(m)
  × direction(m)
```

Contributions from one event cluster are capped. The bounded evidence sum updates an explicit base rate on log-odds scale:

```text
posterior_probability = logistic(logit(base_rate) + evidence_scale × evidence_sum)
```

This is an interpretable prior model, not fitted proof. Confidence is separate from probability. It depends on source coverage, independent clusters, non-company corroboration and measurement quality, with caps for thin/single-source evidence.

### 6. Later statistical models

Only after a sufficiently large, temporally separated sample exists:

- regularised logistic regression for binary outcomes;
- ordinal regression for severity;
- elastic-net linear regression for continuous financial changes;
- calibrated probabilities using an untouched later validation window.

Tree ensembles or language-model-derived scores are not MVP defaults because the current sample cannot justify them and they make attribution harder. Text extraction may later suggest candidate evidence, but a deterministic pipeline owns the final score.

### 7. Evaluation

Evaluation is walk-forward: train/freeze on earlier dates, predict a later period, then reveal outcomes. Comparators include base rate, margin deterioration, inventory/revenue divergence and financial stress count.

Required reporting:

- Brier score and calibration;
- precision/recall and PR-AUC for imbalanced outcomes;
- top-quintile lift;
- median lead time;
- source coverage and missingness;
- family ablations and financial-only versus non-financial versus combined models.

The existing three-company retrospective pilot is only a feasibility test. It did not beat the best simple financial comparator.

## Data ownership and cost

- No paid source is part of the MVP.
- No API key is committed.
- No applicant personal data is collected.
- No publishing, GitHub push or external deployment occurs without permission.
- Every automated claim must be reproducible from preserved evidence.

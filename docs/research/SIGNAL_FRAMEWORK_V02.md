# Outside-in signal framework v0.2

Status: proposed preregistration for review. No v0.2 data collection or model fitting should begin until this framework is accepted and frozen.

## 1. What the model should predict

The previous pilot mixed adverse pressure with positive expansion. Version 0.2 uses separate targets.

### Model A — operational pressure

Predict within 6, 12 and 18 months:

- adjusted operating-margin deterioration of at least 150 bps;
- cash-conversion deterioration of at least 20 percentage points;
- explicit profit warning;
- material restructuring, site closure or consolidation;
- material impairment linked to operations or integration;
- supplier, quality, delivery or working-capital remediation programme;
- material inventory correction.

### Model B — expansion and transformation

Predict within 6, 12 and 18 months:

- previously unannounced capacity investment above 2% of revenue;
- previously unannounced group-wide ERP, data or operating-model programme;
- sustained employee/job-demand growth;
- margin recovery of at least 150 bps;
- major product, geography or manufacturing expansion.

Already-announced plans are excluded as prediction outcomes. Their later continuation is persistence, not discovery.

### Model C — financial outcomes

Continuous targets, evaluated independently of event labels:

- change in adjusted operating margin;
- change in cash conversion;
- revenue growth relative to sector;
- inventory days and trade-working-capital change;
- analyst-guidance change where a dated, reproducible consensus source is available.

The model does not predict share price.

## 2. Evidence families and initial weight budget

These are **priors**, not fitted claims. They sum to 100 within each model. A family can contribute positively or negatively. Missing data is unknown, not zero.

| Evidence family | Pressure | Expansion | Why it may lead | Principal free source |
|---|---:|---:|---|---|
| Workforce demand and skills | 15 | 22 | Hiring mix can expose bottlenecks, replacement demand, new capability and site build-out | Company careers pages; ATS feeds where publicly accessible |
| Operational disclosure and language change | 16 | 10 | New/repeated language on delivery, quality, input cost, utilisation, backlog or execution often precedes quantified results | RNS/company regulated announcements, results transcripts and presentations |
| Leadership and organisational change | 12 | 12 | Operations, supply-chain, quality, transformation and finance leadership changes can signal intervention or readiness | Company announcements; Companies House officers; governance pages |
| Capacity, sites and physical footprint | 10 | 16 | Permits, openings, closures, new lines and footprint changes precede volume and fixed-cost effects | Company news, planning portals where usable, property/site announcements |
| Procurement, contract and order activity | 9 | 12 | Awards, lost contracts and tender patterns change backlog and delivery requirements | Contracts Finder / Find a Tender; company contract announcements |
| Product, quality and customer evidence | 12 | 8 | Recalls, certifications, warranty language, complaints and delivery failures can precede margin and remediation | GOV.UK product recalls, regulator notices, company disclosures |
| Corporate actions and legal structure | 7 | 6 | Charges, acquisitions, subsidiaries, officer churn and insolvency indicators alter execution risk | Companies House API and filings |
| Web and narrative behaviour | 7 | 6 | Careers-page restructuring, strategy-page changes and narrative divergence can reveal shifting priorities | Company sites and archived snapshots; official social posts only as weak evidence |
| Sector and macro context | 7 | 4 | Separates company-specific changes from industry shocks | ONS production, vacancies, prices, BICS and trade series |
| Financial state | 5 | 4 | A deliberately small anchor: controls for what simple financial models already know | Annual/interim accounts and regulated results |

The non-financial evidence budget is therefore 95% before reliability, relevance and availability adjustments. This does not guarantee non-financial dominance: weak or duplicated observations are heavily discounted.

## 3. Metric catalogue

### 3.1 Workforce demand and skills

| Metric | Construction | Interpretation | Contradiction / confounder |
|---|---|---|---|
| Vacancy intensity | unique live vacancies / latest employee estimate | Scale-adjusted labour demand | Outsourced recruiting, acquisition, stale adverts |
| Vacancy acceleration | 13-week count versus preceding 13 weeks and sector index | Demand or intervention is accelerating | Seasonality; new ATS coverage |
| Vacancy persistence | median weeks live; share live over 60 days | Hiring difficulty or ghost/stale roles | Evergreen pipelines |
| Replacement signature | repeated same role/site after removal; no net function growth | Churn or hard-to-fill work | Multiple genuinely identical roles |
| Operations-role share | operations, production, maintenance, planning and logistics roles / all roles | Operational capacity requirement | Normal mix for sector |
| Quality-role share | quality, validation, supplier-quality and regulatory roles / all roles | Quality/remediation or regulated growth | New certification/product launch |
| Supply-chain-role share | procurement, sourcing, supplier-development and logistics roles / all roles | Supply constraint or procurement redesign | Centralisation programme |
| Transformation-role share | ERP, data, automation, PMO and change roles / all roles | Transformation readiness/intervention | Routine IT hiring |
| Seniority shift | manager/director roles versus trailing baseline | Leadership intervention | Planned succession |
| Skill novelty | new skills/technologies absent from prior 12-month postings | New capability or strategic pivot | Job-description template change |
| Geographic/site concentration | vacancy growth concentrated at a plant or new region | Site bottleneck or expansion | Recruiter location miscoding |
| Removal velocity | proportion removed within 30/60/90 days | Approximate filling/withdrawal rate | Advert expiry is not confirmed hiring |

Job records must store first_seen, last_seen, source URL, title, description hash, location, function, seniority and duplicate cluster. “Removed” never means “filled” without corroboration.

### 3.2 Operational disclosure and language

Metrics are quarter/company changes relative to the company's own trailing history and sector peers, not raw word counts.

- delivery-delay, lead-time and on-time-delivery language;
- supplier shortage, sole-source, expedited freight and input-availability language;
- quality, rework, scrap, warranty, recall and customer-acceptance language;
- labour availability, overtime, absenteeism and skills-shortage language;
- utilisation, under-absorption, downtime, maintenance and yield language;
- backlog growth relative to revenue/output growth;
- working-capital, inventory-build and cash-conversion language;
- restructuring, footprint, simplification and productivity language;
- ERP, data, automation and digital-programme language;
- uncertainty/modal language and repeated deferral (“expected”, “later”, “timing”);
- narrative contradiction: improvement claim versus hard indicators;
- narrative novelty: a risk or intervention appearing for the first time.

Measure frequency, novelty, persistence, materiality and specificity. Boilerplate and copied text are clustered and downweighted.

### 3.3 Leadership and organisation

- CEO/CFO/COO/operations/supply-chain/quality/CIO/CDO appointment and departure counts;
- unplanned tenure under 24 months;
- interim appointments;
- creation of transformation, operational-excellence or restructuring roles;
- board risk/audit committee changes;
- subsidiary-director churn from Companies House;
- span of simultaneous senior vacancies;
- acquisition integration leadership and reporting-line changes.

CEO/CFO changes are not assumed adverse. Relationship to pressure depends on timing, stated reason, tenure and corroborating evidence.

### 3.4 Capacity and footprint

- new facility, production line or major equipment announcement;
- announced capex as percentage of revenue;
- closure, consolidation, sale-and-leaseback or footprint reduction;
- planning applications or permits linked confidently to a company/site;
- manufacturing-site additions/removals on company location pages;
- capacity language relative to order/backlog growth;
- maintenance shutdowns and commissioning delays;
- energy-connection or environmental-permit changes where accessible.

Expansion and constraint contributions are stored separately. An expansion is not operational pressure without evidence that current capacity is constraining execution.

### 3.5 Procurement, contracts and orders

- public contract award value / revenue;
- count and value acceleration versus trailing baseline;
- renewal concentration and contract expiry exposure;
- named supplier wins/losses and framework appointments;
- order intake, book-to-bill and order-book coverage;
- cancellation, delay or customer-acceptance events;
- procurement notices naming the company or high-confidence subsidiaries;
- customer concentration and multi-year versus spot order mix.

Contracts Finder data is supplementary: absence is not negative evidence and name matching must be exact or manually confirmed.

### 3.6 Product, quality and customer

- official product-safety recalls and regulator notices;
- warranty/provision change relative to revenue;
- certification suspension, warning or new accreditation;
- customer rejection/acceptance delays;
- complaint or review aggregates only where stable, lawful and sufficiently numerous;
- service-status incidents for industrial-technology firms;
- tender debarment, enforcement or litigation directly tied to operations.

Anonymous individual reviews and social posts cannot independently create a high-strength signal.

### 3.7 Corporate actions and legal structure

- acquisition/divestment count, value and integration age;
- goodwill/intangible concentration and later impairment risk;
- new/settled charges;
- subsidiary formation, closure and registered-office movement;
- filing lateness and qualified accounts;
- officer appointment/resignation clusters;
- insolvency and strike-off indicators;
- ownership/control changes.

### 3.8 Web and narrative behaviour

- material additions/removals on careers, strategy, locations and leadership pages;
- change in advertised strategic priorities;
- press-release cadence and topic mix relative to company baseline;
- deletion or quiet replacement of prior targets, recorded only from archived snapshots;
- executive social posts as leads requiring corroboration;
- reputable reporting as independent corroboration, not as a duplicate of company PR.

### 3.9 Sector controls

- sector output and production indices;
- producer/input prices and energy-price indices;
- ONS vacancy and online-job-ad indices;
- BICS workforce, price, supply-chain and trading measures;
- vehicle/steel/aerospace production where an authoritative industry series exists;
- exchange-rate exposure;
- sector-wide inventory change.

Every company signal is residualised or percentile-ranked against the closest available sector/size peer series. Sector evidence explains away pressure; it does not erase company-specific divergence.

## 4. Source feasibility and reliability priors

| Source | Historical firm-level availability | Forward collection | Reliability prior | Use |
|---|---|---|---:|---|
| Audited accounts | Strong | Strong | 1.00 | Facts and outcomes |
| RNS/regulatory disclosure | Strong | Strong | 0.95 | Dated facts, plans and outcomes |
| Companies House | Strong | Strong; free key required | 0.95 | Identity, filings, officers, charges |
| ONS datasets | Strong, with vintage care | Strong | 0.95 | Sector controls only |
| Contracts Finder / Find a Tender | Moderate | Strong | 0.90 | Awards and procurement evidence |
| Official recall/regulator notice | Moderate | Strong | 0.90 | Quality and compliance events |
| Company results/trading statement | Strong | Strong | 0.80 | Facts and management narrative |
| Company operational/press release | Strong | Strong | 0.70 | Events, subject to self-reporting |
| Company careers/ATS page | Usually weak historically | Strong from first collection date | 0.60 | Workforce-demand facts |
| Archived company webpage | Patchy | Strong once captured ourselves | 0.55 | Page change and historical corroboration |
| Reputable external reporting | Moderate | Strong | 0.60 | Independent corroboration |
| Review aggregate | Weak/unstable | Moderate | 0.40 | Low-weight customer/employee context |
| Executive social post | Patchy | Moderate | 0.25 | Lead only |

Firm-level historical job adverts are the largest free-data gap. ONS/Adzuna supplies a useful sector baseline from 2018, but not a free company-level historical archive. Therefore:

1. do not fabricate a historical job series from current pages;
2. search archived company career pages and public ATS endpoints, recording coverage;
3. treat missing archive coverage as missing;
4. begin a prospective weekly snapshot now for later validation;
5. do not buy a jobs dataset without a separate cost/benefit decision.

## 5. Signal calculation

For observation `i` and condition `c`:

```text
contribution(i,c) =
  family_budget(c)
  × normalised_strength
  × source_reliability
  × measurement_quality
  × materiality
  × family_recency
  × independence
  × condition_relevance
  × direction
```

All multiplicands except direction are bounded 0–1. Direction is −1 to +1. Components and pre-clipped contribution are stored.

### Guardrails

- Maximum contribution from one document/event cluster: 20% of a condition's total evidence mass.
- Maximum contribution from self-published company sources: 60% of evidence confidence.
- A condition needs two independent clusters before confidence can exceed 0.55.
- It needs one non-company source before confidence can exceed 0.70.
- Repeated copies of one announcement have total independence weight 1.0, not one each.
- Absence of a job, press release or filing is not evidence unless source coverage is demonstrably complete.
- Contradictory evidence uses the same weighting machinery as support.
- Alternative explanations are scored as competing hypotheses, not prose appended afterward.

## 6. Normalisation and decay

Use company-relative z-scores/percentiles over a trailing 24-month baseline where available, then sector-relative percentile. With shorter history, mark measurement quality lower rather than pretending stability.

Initial half-lives:

| Signal | Half-life |
|---|---:|
| Vacancy spike | 90 days |
| Persistent skill/function shift | 270 days |
| Executive departure | 365 days |
| Delivery/quality event | 180 days |
| Repeated operational language | 270 days |
| Contract award/order event | Contract-specific; default 365 days |
| Capacity/site change | 730 days |
| Acquisition/integration risk | 730 days |
| Financial structural deterioration | 540 days |
| Recall/enforcement event | 540 days |

These are testable assumptions. Ablations should vary them rather than optimise them on the final holdout.

## 7. How weights will be validated

Hand weights are only model v0.2 priors. They must not be tuned repeatedly on the same outcomes.

1. Freeze feature definitions, family budgets, cutoffs and labels.
2. Build a development set and a later untouched temporal holdout.
3. Compare: financial-only; each family alone; cumulative family additions; hard evidence only; narrative only; all non-financial; full model.
4. Estimate regularised logistic/ordinal models only when sample size supports them; retain the transparent weighted model as the benchmark.
5. Report Brier score, PR-AUC, calibration, top-quintile lift and lead time by outcome family.
6. Keep a family only if it improves out-of-time performance or materially improves calibration/lead time without unacceptable false positives.
7. Report coverage as well as performance: a source that predicts well for only 10% of firms is not a universal signal.

No weight is accepted because it produces a positive result on the three original companies.

## 8. Recommended collection order

### Historical, free and usable now

1. All regulated announcements, results presentations and annual/interim reports—not one document per company.
2. Companies House filing history, officers, charges and subsidiaries.
3. Official contract awards and company order announcements.
4. Official recalls, regulator notices and certifications.
5. ONS vintage sector controls.
6. Archived company strategy, leadership, locations and careers pages where coverage exists.

### Prospective collection beginning now

1. Weekly careers/ATS snapshots with hashes and deduplication.
2. Weekly company-page diffs for careers, leadership, locations and strategy.
3. New regulatory announcements and contract awards.

### Later or only after evidence of value

- paid historical jobs data;
- licensed news/event data;
- employee/customer-review providers;
- patent and trade data enrichment.

## 9. Minimum evidence package per company-date

A company-date is eligible for the next model test only if it has:

- two years of annual/interim financial disclosures;
- all regulated announcements for the preceding 12 months;
- verified Companies House identity and officer/filing history;
- sector controls for the prediction period;
- at least two non-financial evidence families with known coverage;
- explicit source-coverage flags for jobs, procurement, recalls and web archives.

This prevents a sparse company from being scored as healthy simply because nothing was collected.

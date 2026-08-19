# PIOTW Index & Benchmark Framework Specification v0.1

**Methodology version:** 0.1.0  
**Status:** DEVELOPMENT-ONLY / NOT VALIDATED / NOT A PIOTW RATING  
**Scope:** construct, feature and implementation contracts; no production scoring engine

## 1. Constructs

The **PIOTW Operational Index** is a standardised, evidence-based measure of a company’s observable operational condition and trajectory, derived from public disclosures and evaluated relative to comparable companies at a defined point in time.

It is not a credit rating, financial-health score, share-price prediction, management-quality score or generic company-quality score. Its target interpretation is 100 = operationally very strong relative to peers, 50 = approximately peer median, and 0 = operationally very weak relative to peers. This is a target design, not a validated scale.

Three constructs remain separate:

- **PIOTW Pressure Index:** how much adverse operational pressure appears to be accumulating.
- **PIOTW Momentum:** whether operational condition is improving or deteriorating, including direction, rate and stability.
- **Evidence Confidence:** how strong, independent, recent and complete the evidence base is. Confidence must never be interpreted as performance.

A company can be operationally strong and simultaneously show high pressure. A confident weak assessment is different from an uncertain assessment.

## 2. Six dimensions

1. **Cost & Efficiency** covers cost conversion, productivity, margin pressure and operating leverage.
2. **Capacity & Footprint** covers utilisation, physical capacity, sites and fixed-cost absorption.
3. **People & Organisation** covers workforce capacity, skills, structure and leadership continuity.
4. **Supply Chain & Delivery** covers sourcing, quality, inventory, logistics and customer delivery.
5. **Technology & Execution** covers transformation delivery, systems change, automation and implementation reliability.
6. **Growth & Investment** covers deployment and productive conversion of growth capital and acquisitions.

The dimension registry gives purposes, phenomena, positive, negative and ambiguous examples, candidate financial links and possible future outcomes. These dimensions are candidates pending construct-validity and redundancy testing.

## 3. Evidence-to-feature transformation

The feature registry is a contract for candidate model inputs, not proof that the current Evidence Engine supports every field at production quality. Feature values must retain evidence IDs, publication/information-available dates, reporting periods, extraction versions and review status.

### Frequency

Raw mention counts alone are prohibited as a production measure. Candidates include occurrences per 10,000 eligible words, distinct independent documents containing a signal, and distinct reporting periods containing it. Document length, disclosure frequency and source type must be controlled.

### Recency

Recent evidence normally has more relevance, but v0.1 selects no decay weight. Configurable candidates are step windows, exponential decay and piecewise decay. The selected function, parameters, event date choice and cutoff handling must be versioned and fitted or justified without outcome leakage.

### Persistence

One-off, recurring and continuously persistent signals must be distinguishable. Candidate representations include number/share of eligible periods, consecutive periods and time since first/last supported occurrence. Repeated language within one reporting cycle is not persistence.

### Direction and acceleration

Where a measurable level exists, retain current level, change, rate of change and direction separately. Acceleration/deceleration is a longitudinal construct and must not be inferred from adjectives alone. No thresholds are selected in v0.1.

### Severity

Severity may enter only when defined consistently in the evidence layer. Quantified amount/roles/sites/duration, materiality language and operational scope are candidate components. Severity scales must be source-grounded, ordered and validated; absence of a quantified amount is not zero severity.

### Confidence

Evidence confidence may gate, attenuate or create an uncertainty interval around a feature. The treatment is unresolved. Low-confidence evidence must not contribute identically to reviewed high-confidence evidence, and confidence must remain separately visible.

### Independence and duplication

Copied wording across annual, interim, results and investor documents must not automatically count as independent corroboration. Candidate deduplication uses normalised-span similarity, same underlying event, reporting cycle, source lineage and cross-reference. Multiple documents may strengthen source traceability without increasing event frequency.

## 4. Polarity and context

Every feature is `positive`, `negative`, `neutral/context` or `bidirectional`. Positive/negative means the evidenced direction is normally associated with operational strength/weakness, subject to testing. `neutral/context` features are non-directional modifiers. `bidirectional` features require an observed direction or explicit context before they can affect health.

Context-dependent features are ineligible for the health index unless a versioned rule resolves demand, delivery, benefit or adverse context. Pressure eligibility can differ: an announced cost programme may indicate pressure while offering possible future benefit. Eligibility flags do not imply a weight.

## 5. Missingness, coverage and evidence sufficiency

Missing is not zero, normal or peer median. Each output must distinguish no disclosure, unavailable source, unsupported extraction, not applicable and genuinely observed absence where that can be established. Minimum evidence count is a gate, not a production threshold. Future aggregation requires empirically tested minimum feature and dimension coverage. Scores must expose missingness and evidence confidence.

## 6. Dimension and overall index logic

Version 0 experiments may use equal weighting across eligible features within a dimension for transparency. Context-dependent, ineligible, missing or insufficient-evidence features are not silently forced into the calculation. Version 1+ weights may change only for documented predictive validity, redundancy, stability, domain evidence or calibration reasons.

Each future dimension output must expose dimension score, peer percentile or benchmark context, trend, evidence confidence, feature contributions and missingness. The target overall index is a configurable weighted combination of eligible dimension scores. The first experiment uses equal dimension weights; this is a test scaffold, not a production formula. Arbitrary expert weights must not be silently introduced.

The `index-config.example.json` records the methodology version and exact experimental weights. Once a configuration is frozen for a validation run it is immutable; any change requires a new version.

## 7. Provisional display bands

The example bands A+ 85–100, A 75–84, B 65–74, C+ 55–64, C 45–54, D 35–44, E 20–34 and F 0–19 are **PROVISIONAL / NOT EMPIRICALLY CALIBRATED**. They must not be presented as a real rating. Final bands require empirical distributions, outcome calibration, stability testing and decision-usefulness evidence.

## 8. Historical score and momentum

A future score snapshot must be point-in-time and reproducible using only information available at its cutoff. Longitudinal outputs should support 12-month and 24-month change, trend classification, acceleration/deceleration and volatility/stability. Reporting-cycle alignment and restatements must be handled explicitly. No change or trend thresholds are chosen here. A deteriorating trajectory may ultimately be more predictive than an absolute level; that is a hypothesis to test.

## 9. Pressure Index

The Pressure Index measures accumulation, persistence, recency and severity of adverse operational signals such as restructuring, margin pressure, delivery disruption, workforce reduction, footprint rationalisation, supply-chain stress and execution delay. It does not simply invert the Operational Index: positive operating capacity can coexist with intensifying adverse pressure, and pressure signals may precede realised deterioration. No production formula, weights or bands are defined.

## 10. Financial linkage and intervention frameworks

The financial-linkage registry maps features/dimensions to financial-statement areas, a falsifiable hypothesis, confidence and validation status. These are associations to test, not causal claims.

The intervention registry is a taxonomy of review classes. Each class has related dimensions/signals, potential financial areas, evidence prerequisites and limitations. It is not company-specific advice and cannot prescribe unsupported actions such as closing a particular site.

## 11. Scientific rules

1. No score without a defined construct.
2. No feature without a documented definition.
3. No weighting without rationale or empirical support.
4. No peer percentile without a sufficiently sized peer cohort.
5. No prediction without validated outcome testing.
6. Evidence confidence is separate from operational performance.
7. Financial linkage is not financial causation.
8. Context-dependent features must not be forced into positive/negative scoring.
9. Methodology versions are immutable once frozen for a validation run.
10. The index must demonstrate incremental value over simple financial baselines.

## 12. Open questions

- Are the six dimensions construct-valid, exhaustive and non-redundant?
- Which candidate features are extractable reliably and belong in each construct?
- Which recency function and parameters generalise out of sample?
- How should intermittent versus consecutive persistence be treated?
- Should confidence gate, attenuate or express uncertainty around contributions?
- Which cohort filters and fallbacks produce fair, stable comparisons?
- Are 50/30/20 valid minimum peer thresholds?
- When should features or dimensions depart from equal weighting?
- Should the user-facing mapping use empirical CDF, percentile or robust-z-to-percentile?
- What rating thresholds, if any, are calibrated and decision-useful?
- What formula distinguishes pressure accumulation from poor health?
- How should capacity, capex, acquisition and other context-dependent signals be resolved?
- Which missing-data and minimum-coverage strategy is least biased?
- What adverse and positive outcome taxonomy is reliable across sectors?
- What corpus size, sector breadth and history are required for validation?

Until these questions pass the validation plan, no output may be called a real PIOTW Rating.

# MVP completion status

## Completed locally

- [x] Product research question and defined 6/12/18-month outcomes
- [x] Separate pressure and expansion model specifications
- [x] Continuous financial-outcome specification
- [x] Ten-family signal catalogue with 54 machine-readable features
- [x] Initial family weights and feature half-lives
- [x] Point-in-time evidence, coverage, contribution and prediction schemas
- [x] Deterministic weighted scoring, decay, cutoffs, contradiction handling and cluster caps
- [x] Confidence separated from probability
- [x] Greenhouse, Lever, Ashby, SmartRecruiters and Recruitee adapters
- [x] Workday/Workable/Teamtailor and common ATS detection/access boundaries
- [x] Robots-aware structured careers/page collection that fails closed
- [x] Historical job snapshot storage and no-longer-observed handling
- [x] Deterministic workforce feature extraction
- [x] Companies House, ONS, Contracts Finder and SEC clients
- [x] First-party page-change snapshot storage
- [x] Binary evaluation: Brier, calibration, precision/recall, average precision and lift
- [x] Existing cutoff/provenance validation preserved
- [x] v0.2 integration demonstration generated from checked evidence
- [x] Dashboard system map, source map, weights and connected v0.2 demonstration
- [x] Production frontend build and browser interaction/console verification
- [x] Dependency-light end-to-end self-check

## Deliberately not claimed as complete evidence

- [ ] Prospective weekly history: time must pass after the first authorised snapshot
- [ ] Full historical cohort: requires collecting and manually validating more public records
- [ ] Model validation: requires an adequately sized temporal development/holdout sample
- [ ] Statistical coefficient fitting: prohibited until sample size supports it
- [ ] Commercial or predictive superiority: contradicted by the current tiny pilot
- [ ] Public deployment: not authorised

## Definition of “MVP complete”

The software path is complete when a configured source can be collected, preserved with provenance, transformed into an observation, scored at a historical cutoff, displayed with its evidence and evaluated once an outcome is supplied. That path is implemented locally.

The research is not “complete” in the sense of proving that the model works. No honest architecture can manufacture the missing time series or validation sample. The MVP is designed to accumulate that evidence without changing the rules after seeing results.

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
- [x] Ranked five-target event taxonomy with objective resolution contracts
- [x] Canonical entity aliases and deterministic event-deduplication primitives
- [x] Operational SQLite migration with keys, indexes and collector-run provenance
- [x] Database-enforced immutable prediction and prediction-resolution registry
- [x] Fully persisted Bodycote evidence → event → feature → prediction → outcome → backtest slice
- [x] Read-only localhost API for companies, predictions and backtests
- [x] Dashboard prediction-registry view backed by the persisted slice
- [x] Deterministically selected ten-company restructuring cohort at two historical cutoffs
- [x] Twenty pre-outcome predictions committed before outcome inspection
- [x] Separate 20-row outcome ledger with exclusions, evidence and immutable SQLite registration
- [x] Reproducible validation metrics and protocol-deviation report
- [x] Validation dashboard backed by generated results
- [x] Ten first-party prospective sources enabled; seven initial permitted snapshots stored and three fail-closed statuses recorded

## Deliberately not claimed as complete evidence

- [ ] Prospective weekly history: time must pass after the first authorised snapshot
- [ ] Independent outcome adjudication: the current 20 labels were resolved by one researcher
- [ ] Clean comparator validation: numeric simple-rule definitions must be frozen before the next untouched outcome set
- [ ] Model validation: requires an adequately sized genuinely untouched temporal holdout sample
- [ ] Statistical coefficient fitting: prohibited until sample size supports it
- [ ] Commercial or predictive superiority: not established by this feasibility sample
- [ ] Public deployment: not authorised

## Definition of “MVP complete”

The software path is complete when a configured source can be collected, preserved with provenance, transformed into an observation, scored at a historical cutoff, displayed with its evidence and evaluated once an outcome is supplied. That path is implemented locally.

That working prototype is now implemented and browser-verified. The research is not “complete” in the sense of proving that the model works. The ten-company result is promising on ranking and probability error, but its formal gate remains indeterminate because two comparator thresholds were not numerically frozen and labels lack independent adjudication. The next scientific step is a clean preregistration and untouched temporal holdout, while weekly snapshots accumulate without rewriting prior predictions.

# Restructuring validation protocol v1

Frozen: 13 August 2026, before outcome collection  
Status: confirmatory feasibility test; not a statistically powered product-validation claim

## Question

Using only evidence publicly available at a historical cutoff, does the frozen PIOTW rules model predict a **previously unannounced material restructuring within 12 months** better than declared naive baselines?

## Cohort and prediction occasions

The candidate frame is the existing 30-company UK-listed industrial frame. The three exploratory-pilot companies are excluded because their outcomes have already been inspected. Dowlais is excluded because it was not an independently listed operating company at both cutoffs. `scripts/select_restructuring_validation.py` hashes the fixed seed plus ticker, then selects the lowest hashes under fixed quotas: three aerospace/automotive, three materials and four engineering/technology companies.

Each selected company receives predictions at 31 December 2021 and 31 December 2022, producing 20 prediction occasions. A company may remain in the cohort after a first outcome, but the second occasion predicts only a distinct post-cutoff qualifying programme not publicly announced before that cutoff.

## Outcome contract

Positive means the first post-cutoff public announcement, within 365 days, of at least one of:

- a named or explicitly described group/division restructuring or reorganisation programme;
- a site closure or consolidation programme;
- a redundancy/consultation programme affecting at least 5% of group employees, at least 100 roles, or described by the issuer as material;
- a group/division cost programme with quantified recurring savings of at least 2% of the latest pre-cutoff annual operating costs, or described as material/significant and accompanied by exceptional/restructuring charges;
- a material disposal/exit explicitly undertaken as operational restructuring rather than ordinary portfolio management.

Routine continuous improvement, isolated management appointments, already-announced plans, unquantified local adjustments, acquisitions, ordinary disposals and capacity expansion alone are excluded. If evidence cannot determine materiality, label `ambiguous` and exclude that occasion from primary scoring rather than forcing a class.

`outcome_date` is the first public availability date of the qualifying announcement. Outcome evidence must be a regulated/company disclosure or filed annual/interim report. Absence is resolved negative only after checking the issuer's announcement/results archive across the full horizon and the first results document published after the horizon.

## Information boundary

Evidence is eligible only where `available_at <= 23:59:59 UTC` on the cutoff. A reporting-period date never substitutes for publication date. Pre-cutoff evidence mentioning the same programme places that programme on the exclusion list; later repetition is not a new outcome. Documents first found after prediction registration may be added only if their historical availability is independently evidenced, and require a new prediction version—not mutation of a registered prediction.

## Evidence and features

Use the latest annual/interim/trading disclosures available before each cutoff, plus eligible point-in-time operational sources actually archived by the cutoff. Extract both pressure and contrary evidence. Each observation records exact source URL, availability date, document hash, page/location, verbatim-bounded observation, direction, strength, reliability, materiality, independence and extraction method.

The restructuring model version and weights are frozen before outcome inspection. Probability and confidence remain separate. A prediction records ordered evidence IDs and a feature/configuration hash. Prediction rows cannot be updated or deleted.

## Baselines

1. Constant 12% prior fixed in `config/prediction_targets.json`.
2. Leave-one-company-out development base rate, reported only as sensitivity because n is small.
3. Financial-stress rule based solely on pre-cutoff margin deterioration, negative cash flow and inventory/revenue divergence.
4. Disclosure-language rule triggered by explicit pre-cutoff cost, efficiency, closure, redundancy or restructuring language, excluding an already-announced qualifying programme.

No baseline is tuned after validation outcomes are seen.

## Evaluation and gate

Primary metric: Brier score versus the constant prior and each simple rule. Also report calibration buckets, precision/recall at the frozen 0.5 threshold, average precision, lift in the highest-risk group, lead time, and every false positive/negative. Ambiguous outcomes are reported and excluded from primary metrics.

Proceed to a 30-company development cohort only if PIOTW beats every declared simple comparator on Brier score and shows either useful ranking/lift or median lead time of at least 90 days. Otherwise stop expansion and revise or reject the target/signal hypothesis. No proprietary-intelligence, calibration or commercial-superiority claim is permitted from this sample.

## Separation of work

The prediction dataset and immutable registry must be generated and committed before opening or coding post-cutoff outcome documents. Outcome resolution is stored in separate files/tables with its own evidence hashes. The final report must record any protocol deviation.


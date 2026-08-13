# Existing work inventory and consolidation record

Decision date: 13 August 2026  
Canonical working copy: `/Users/roseattridge/Documents/ChatGPT/PIOTW MVP CODEX`  
Status: one consolidated repository

## Material discovered

The substantive earlier implementation was found in ChatGPT Work's internal project storage under project `g-p-6a7c4cb078d08191a30a6a3b888c76c2`. It contained a clean Git repository with five commits:

1. `a50156f` — retrospective PIOTW intelligence pilot;
2. `ebbbc3c` — broader outside-in signal framework;
3. `9daf9a8` — public careers and official-data collectors;
4. `2a4a3ee` — auditable intelligence MVP architecture;
5. `03b5175` — immutable event-prediction vertical slice.

The repository included the React/Vite research dashboard; Python scoring, entity, event, outcome and backtest modules; PostgreSQL and SQLite migrations; point-in-time careers and first-party page collectors; Companies House, ONS, Contracts Finder and SEC clients; signal catalogue and weights; source fixtures and checked evidence; five target definitions; tests; API; and research/methodology documents.

## Decisions and completed work retained

- Evidence, events, features, interpretations, predictions and outcomes remain separate and traceable.
- Pressure and Expansion remain independent dimensions; no generic company score is introduced.
- Predictions are target-specific, versioned and database-enforced as immutable.
- Historical evaluation uses `available_at` cutoffs, frozen evidence IDs and independently resolved outcomes.
- The deterministic weighted model remains the honest first model; AI scoring stays disabled.
- The four primary source families remain regulated/company disclosures, careers/ATS data, Companies House and Contracts Finder, with ONS as a control.
- The existing collectors, dashboard, operational schema, real three-company feasibility pilot and Bodycote vertical slice are authoritative.
- The pilot's negative result is retained: the operational model did not beat its strongest simple comparator. It is feasibility evidence, not proof of predictive value.

## Duplicate approach reconciled

A second, small uncommitted scaffold was created in the Documents folder before the internal ChatGPT Work repository was located. It implemented a synthetic restructuring fixture, a SQLite schema, an immutable prediction trigger, cutoff tests and concise documentation. It was not selected as a competing version because the earlier repository already implemented these controls more comprehensively and also contained real checked disclosures, collectors, a dashboard and Git history.

The mature repository has therefore replaced that scaffold in the Documents folder. The useful operational addition retained from the scaffold is a root `Makefile` exposing consistent `make demo`, `make test`, `make build` and `make api` commands. No synthetic result or duplicate schema was imported.

## Contradictions resolved

- **First target:** the product blueprint ranks capacity expansion first and restructuring second, while the newer brief defaults to restructuring. The existing completed vertical slice predicts operating-margin deterioration. No historical record is rewritten. The next prospective target experiment should use restructuring within 12 months, while all three remain explicitly versioned targets.
- **Python version:** the mature project supports Python 3.11+; the duplicate requested 3.12+. Retain 3.11+ until a dependency or deployment requirement justifies narrowing it.
- **API:** retain the dependency-light local HTTP API. FastAPI is a later deployment option, not a current requirement.
- **Database:** retain SQLite locally and the existing PostgreSQL migration path.

## Gaps still requiring validation

- An adequately sized temporal development and untouched holdout cohort;
- calibrated target base rates and weights;
- prospective weekly source history;
- source licensing and retention review before public/commercial use;
- evidence that operational signals improve calibration, lift or lead time over simple baselines;
- deployment, spending and public claims, none of which are authorised by consolidation.

## Ongoing working rule

All future implementation happens only in the canonical Documents repository above. Git commits provide local history. A private GitHub remote should be added when authorised so this machine is not the only durable copy. ChatGPT internal project folders are not working copies and must not be used for future development.


# Put It On The Wall Intelligence

An auditable, outside-in operational-intelligence research MVP. It includes a real 20-occasion historical feasibility validation and a live first-party snapshot collector, but must not be presented as validated commercial intelligence.

**Canonical working copy:** `/Users/roseattridge/Documents/ChatGPT/PIOTW MVP CODEX`. This is the only repository to use for future development. The discovery and consolidation history is recorded in `docs/EXISTING_WORK_INVENTORY.md`.

## What is working

- Responsive React research UI with company universe, profile, evidence ledger and honest placeholders for later views.
- PostgreSQL migration for complete provenance, facts/signals/hypotheses/predictions separation, versions, costs, benchmarks and experiments.
- Deterministic weighted scoring and confidence calculation.
- Backtest cutoff enforcement using public `available_at`.
- Source and extractor interfaces, ontology seed, assumption/backtest/methodology documents and unit tests.
- Public careers collection for Greenhouse, Lever, Ashby, SmartRecruiters and Recruitee, ATS discovery, and point-in-time job snapshots.
- Official public-data clients for Companies House, ONS, Contracts Finder and SEC EDGAR.
- AI disabled by default; no secrets; no paid service required.
- Frozen ten-company restructuring validation: 20 immutable predictions, separately resolved outcomes and reproducible metrics.
- Prospective first-party page monitoring configured for the same ten companies; seven initial robots-permitted snapshots collected on 13 August 2026 and three failures recorded explicitly.

## Run locally

Create the local Python environment, install its declared packages, install the JavaScript dependencies, then use the root commands:

```bash
python3.12 -m venv .venv
.venv/bin/pip install 'pydantic>=2' 'pyyaml>=6' pytest
pnpm install
make demo
make test
make build
```

Use `pnpm dev` for the dashboard development server. Copy `.env.example` only when connecting later services. Never commit the resulting `.env`.

Python 3.11 or newer is required; do not use the macOS Command Line Tools Python 3.9.

Run `python scripts/self_check.py` for the dependency-light end-to-end verification. `python scripts/build_v02_demo.py` regenerates the v0.2 architecture demonstration consumed by the dashboard. Public collection is deliberately config-driven: `scripts/collect_careers.py` snapshots enabled ATS/careers sources and `scripts/collect_pages.py` snapshots enabled first-party pages only after their robots policy permits retrieval.

To reproduce the restructuring validation, run:

```bash
.venv/bin/python scripts/register_restructuring_predictions.py
.venv/bin/python scripts/evaluate_restructuring_validation.py
```

The first command recreates the already-frozen registry; it does not generate a new model version. The second joins the separate outcome ledger and publishes the dashboard metrics. Run `.venv/bin/python scripts/collect_pages.py` for the next prospective snapshot. Raw pages remain local under `data/raw/pages`; the tracked status file records coverage and hashes without publishing copied site content.

The root convenience commands are `make demo`, `make test`, `make build` and `make api`.

`python scripts/build_vertical_slice.py` rebuilds the authoritative local SQLite MVP database and the dashboard's immutable Bodycote prediction fixture. `python scripts/serve_api.py` serves read-only company, prediction and backtest JSON on `127.0.0.1:8765`. The full product decisions, ranked targets, delivery plan and cost ceiling are in `docs/PRODUCT_BLUEPRINT.md`.

## GitHub publishing

The frontend is a conventional static Vite application. A manual GitHub Pages workflow is included, but it does nothing until the repository is on GitHub and its **Deploy to GitHub Pages** action is explicitly run. There is no ChatGPT Sites configuration or dependency.

## Scientific status

The original three-company pilot remains as an exploratory record. The newer restructuring validation selected ten companies deterministically, registered predictions before outcome research, and resolved 20 historical occasions. Four positives occurred. PIOTW's Brier score was 0.137896 versus 0.166400 for the frozen 12% prior, with ROC AUC 0.75, 2.5x top-risk lift and median lead time 165.5 days. It nevertheless missed all four at the frozen 0.5 threshold.

The formal gate is **indeterminate, not passed**: two declared simple-rule comparators lacked numerical preregistration and outcome labels have not been independently duplicated. See `docs/research/RESTRUCTURING_VALIDATION_REPORT_V1.md`. The result permits continued prototype development, not a superiority or calibration claim.

The broadened outside-in source plan, access boundaries and initial weights are documented in `docs/research/PUBLIC_DATA_APIS.md` and `docs/research/SIGNAL_FRAMEWORK_V02.md`.

For a plain system description see `docs/ARCHITECTURE.md`; for exact model behaviour and limitations see `docs/MODEL_CARD.md`; for the implemented-versus-not-yet-evidenced boundary see `docs/MVP_STATUS.md`.

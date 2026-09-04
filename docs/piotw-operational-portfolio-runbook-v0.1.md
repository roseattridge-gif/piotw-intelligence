# PIOTW operational portfolio runbook v0.1

## Scope

This runbook operates the development portfolio workflow only. It does not invoke, modify, copy or publish scientific truth, blinded review returns, frozen predictions or evaluation artefacts.

## Configuration and run

The active development portfolio is `config/portfolios/real_development_portfolio_v0_1.json`. Run it from the repository root:

```sh
.venv/bin/python scripts/run_operational_portfolio_v01.py --as-of 2026-09-04T00:00:00+00:00
```

For change detection, pass the prior immutable `portfolio_run.json` using `--previous`. Each company is isolated: a failed company or source becomes an explicit validation item and does not silently remove the rest of the portfolio.

## Scheduling seam

The command is deterministic for the configuration, evidence snapshot and `as-of` instant. A scheduler should call it after approved source collectors complete, retain the previous run path, then build and publish `piotw-web`. Scheduling infrastructure must supply the `as-of` instant and previous-run pointer; neither is guessed by the application.

## Health and freshness

- `/health.json` reports the deployed portfolio run identifier and confirms that no scientific gate ran.
- `/portfolio` shows the latest successful run and latest evidence date separately.
- A stale run is visible rather than converted into a current claim.

## Failure recovery

Re-run a failed company/source with the same frozen evidence and `as-of` value to reproduce the result. Restore an unavailable connector only through its approved source adapter. Never treat missing, failed or stale evidence as zero.

## Security and deployment boundary

Only the web application, operational schemas/configuration, non-sensitive public-evidence fixtures and operational documentation may enter a public deployment commit. Exclude `data/review_returns`, truth directories, review packs, frozen predictions, evaluation outputs and scientific receipts. The truth-bearing branch history is not a deployment source.

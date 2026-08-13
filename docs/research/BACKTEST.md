# Backtest protocol

Use an append-only snapshot for each prediction date. Include documents only where `available_at <= prediction_date`; retain period, publication, availability and retrieval independently. Freeze cohort, labels, model/configuration, exclusions and baseline definitions before outcome inspection. Evaluate 6/12/18-month horizons against five baselines and registered source ablations. Report calibration and uncertainty, not only discrimination. Never rewrite a prediction after its outcome.

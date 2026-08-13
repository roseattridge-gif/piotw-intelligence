"""Run the deterministic, retrospective three-company feasibility pilot."""
import csv, json, math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader((ROOT / "data/evidence_ledger.csv").open()))
by_company = defaultdict(list)
for row in rows:
    values = [float(row[x]) for x in ("strength","reliability","materiality","recency","independence","relevance")]
    contribution = math.prod(values) * int(row["direction"])
    row["contribution"] = contribution
    by_company[row["company"]].append(row)

# Prior 0.20, with a deliberately conservative evidence scale fixed for v0.1.
prior_logit = math.log(0.2 / 0.8)
predictions = {}
for company, evidence in by_company.items():
    evidence_sum = sum(x["contribution"] for x in evidence)
    probability = 1 / (1 + math.exp(-(prior_logit + 1.35 * evidence_sum)))
    confidence = min(0.85, 0.20 + 0.055 * sum(float(x["independence"]) for x in evidence))
    predictions[company] = {"probability": round(probability, 3), "confidence": round(confidence, 3), "evidence_sum": round(evidence_sum, 3)}

labels = {"Chemring": 1, "Vesuvius": 1, "Bodycote": 0}
baselines = {
    "PIOTW operational": {c: predictions[c]["probability"] for c in labels},
    "Margin deterioration": {c: 0.20 for c in labels},
    "Inventory/revenue divergence": {"Chemring": 0.20, "Vesuvius": 0.65, "Bodycote": 0.20},
    "Financial stress count": {"Chemring": 0.20, "Vesuvius": 0.40, "Bodycote": 0.20},
    "Leave-one-out base rate": {"Chemring": 0.50, "Vesuvius": 0.50, "Bodycote": 1.00},
}
metrics = {}
for name, probs in baselines.items():
    brier = sum((probs[c] - labels[c]) ** 2 for c in labels) / len(labels)
    predicted = {c: int(probs[c] >= 0.5) for c in labels}
    tp = sum(predicted[c] == 1 and labels[c] == 1 for c in labels)
    fp = sum(predicted[c] == 1 and labels[c] == 0 for c in labels)
    fn = sum(predicted[c] == 0 and labels[c] == 1 for c in labels)
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    metrics[name] = {"brier": round(brier, 3), "precision_at_0.5": round(precision, 3), "recall_at_0.5": round(recall, 3), "probabilities": probs}

result = {
    "status": "retrospective exploratory pilot; not a blind backtest",
    "prediction_date": "2021-12-31", "horizon_end": "2023-06-30",
    "model_version": "exploratory-0.1.0", "predictions": predictions,
    "labels": labels, "metrics": metrics,
    "limitations": ["n=3", "outcomes were inspected during implementation after protocol freeze", "one retained pre-cutoff disclosure per company", "no statistical or proprietary-alpha claim permitted"],
}
(ROOT / "data/derived/pilot_results.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))

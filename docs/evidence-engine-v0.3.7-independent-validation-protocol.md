# Evidence Engine 0.3.7 independent atomic-observation validation protocol

Status: **PREREGISTERED — DO NOT ALTER AFTER CORPUS COLLECTION**

This study tests whether Evidence Engine 0.3.7 discovers and extracts atomic operational facts from genuinely unseen issuer documents. It does not test event families, dimensions, scores or predictions.

## Frozen selection rule

The corpus comprises the latest official Form 10-K and latest official Form 10-Q available from SEC EDGAR as at 19 August 2026 for each of ten fixed issuers: Adobe, Intuit, ServiceNow, Lam Research, Applied Materials, General Mills, Colgate-Palmolive, Conagra Brands, Waste Management and AutoZone. The company list was chosen before source download from issuers absent from prior PIOTW corpus manifests. Only primary SEC filing documents are eligible. Amendments, exhibits without the filing body, registration statements and documents published after the freeze date are excluded.

The target is 10 companies and 20 documents. Collection fails closed if either required form is unavailable, a company/ticker/CIK overlaps a prior manifest, a URL or source hash overlaps any prior corpus, or an artefact cannot be hashed.

## Independence and contamination

Source-first labels must be produced without access to 0.3.7 output, prior event labels, candidate zones, model decisions, dimensions, scores or predictions. Two independent human reviewers are preferred. If no independent reviewers are available, the study stops after blinded-pack preparation. AI-assisted work is never formal gold and cannot trigger this gate.

The corpus, labels and protocol must each be frozen and hashed before model execution. Any document inspected for model output or tuning becomes spent scientific material. There is one model execution only; no tuning or rerun is permitted.

## Source-first annotation

For every document, reviewers read the source and enumerate all material factual operational observations. Allowed decisions are `YES`, `NO` and `AMBIGUOUS`. A `YES` records subject, action/state, object, timing, polarity, scope, entity relationship and the exact evidence span. Timing is one of `CURRENT`, `ONGOING`, `PLANNED_COMMITTED`, `COMPLETED_RECENT`, `HISTORICAL`, `HYPOTHETICAL`, `UNCLEAR`. Entity relationship is one of `ISSUER`, `SUBSIDIARY`, `CUSTOMER`, `SUPPLIER`, `COMPETITOR`, `INDUSTRY`, `OTHER`, `UNCLEAR`.

Reviewer disagreements are adjudicated blind by a third human reviewer before labels are frozen. Ambiguous cases remain ambiguous and are excluded from positive precision/recall denominators but assessed separately.

## Evaluation units

- Evidence-zone recall: source-first supported observations whose exact or materially equivalent supporting span intersects a discovered zone / all source-first supported observations.
- Irrelevant-zone rate: discovered zones containing no supported or ambiguous source-first observation / all discovered zones.
- Observation precision: supported accepted observations / all accepted observations.
- Observation recall: source-first supported observations materially recovered / all source-first supported observations.
- Ambiguity agreement: ambiguous cases preserved as ambiguous / all gold ambiguous cases surfaced.
- Timing accuracy: materially correct timing / matched supported observations.
- Attribution accuracy: materially correct entity relationship / matched supported observations.
- Exact provenance: accepted observations whose exact evidence pointer is contained in the immutable source / all accepted observations.
- Provider/schema completeness: contract-valid responses / attempted semantic calls.

Matching permits semantic equivalence but not changed subject, action, object, direction, time or accounting/operational identity. Counts and denominators are always reported overall, per company and per document.

## Severe errors

Any of the following is severe: unsupported observation stated as fact; third-party fact attributed to the issuer; hypothetical statement presented as realised; polarity inversion; invented evidence; evidence pointer not contained in source; materially wrong subject/action/object; or malformed output accepted as valid.

## Frozen pass gate

All conditions must pass:

- observation precision >= 0.90
- supported-observation recall >= 0.80
- evidence-zone recall >= 0.90
- severe false positives = 0
- attribution accuracy >= 0.98
- exact provenance = 1.00
- provider/schema completeness >= 0.99

Timing accuracy and ambiguity agreement are reported but are not independent pass conditions because their denominators may be small. Any unreported required metric, contamination failure, label-integrity failure, partial-result inspection, or second execution is an automatic failure.

## Stopping rule

Stop before execution unless protocol, corpus and independent human labels are frozen. After the single run, evaluate once. A pass freezes the observation layer as `EVIDENCE_ENGINE_0_3_7_ATOMIC_OBSERVATION_VALIDATION_PASSED`; a failure records `EVIDENCE_ENGINE_0_3_7_ATOMIC_OBSERVATION_VALIDATION_FAILED` and spends the corpus. Neither result authorises event-family mapping in this task.


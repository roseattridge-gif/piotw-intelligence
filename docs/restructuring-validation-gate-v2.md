# Restructuring validation gate v2

Status: frozen before holdout outcome adjudication

The gate is applied to the untouched temporal holdout only. It is not production approval.

## Integrity prerequisites

Any material leakage, model/specification hash mismatch, manifest mutation after outcome review, unmasked adjudication, or unresolved adjudication integrity failure produces `FAIL` regardless of metrics. At least 50 scored occasions, 40 unique companies and 8 positive events are required for a result above `FAIL`; otherwise the result is `INSUFFICIENT EVIDENCE` and cannot advance.

## Quantitative criteria

All are predeclared:

1. PIOTW Brier skill versus the frozen 12% prior is greater than 0: `1 - Brier(PIOTW)/Brier(prior) > 0`.
2. PIOTW Brier is no more than 0.01 worse in absolute terms than the strongest eligible frozen simple comparator.
3. The tie-aware top quintile has lift greater than 1.0 and contains at least two positive events.
4. ROC AUC is greater than 0.50.
5. Positive events have median lead time of at least 90 days, with event count reported.
6. Removing any one company does not reverse both positive Brier skill and AUC-above-random; no single sector contains more than 60% of all positives or accounts for the entire Brier improvement.
7. At least 90% raw adjudicator agreement where two reviews exist; uncertain cases are excluded and reported.

## Decisions

- `FAIL`: an integrity prerequisite fails, PIOTW is worse than the prior on Brier, AUC is at or below 0.50, or four or more quantitative criteria fail.
- `PROMISING / CONTINUE VALIDATION`: integrity prerequisites pass and at least five of seven quantitative criteria pass, but uncertainty intervals, event count, comparator performance or sensitivity do not support the higher decision.
- `PASS FOR NEXT-STAGE PRODUCT RESEARCH`: integrity prerequisites and all seven quantitative criteria pass, and company-clustered 95% intervals do not show clearly adverse Brier skill or sub-random AUC.
- `INSUFFICIENT EVIDENCE`: minimum occasion/company/positive counts are not reached without an integrity failure.

A pass does not mean statistical proof, production readiness, calibrated commercial probabilities, commercial superiority or proprietary intelligence.

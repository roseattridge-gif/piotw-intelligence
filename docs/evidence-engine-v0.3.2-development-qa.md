# Evidence Engine 0.3.2 development QA

All figures below are development diagnostics, not independent accuracy.

## Frozen engineering target

Before final rerun the target required less than 10% obvious false positives on the five-document set, zero severe false positives, near-zero duplicates, no 0.3.1 regression and retention of genuine supported events.

## 0.3.1 regression

The six-document diagnostic retained 14 event agreements with zero missed AI-reviewed events, zero diagnosed false positives, zero duplicates and zero severe disagreements. The two numerical corrections remain resolved.

## Five-document before/after

| Metric | Before 0.3.2 | After 0.3.2 |
|---|---:|---:|
| Candidates | 165 | 165 |
| Accepted inspected | 61 | 28 |
| Supported | 37 | 28 |
| Obvious false positives | 19 | 0 |
| Ambiguous among accepted | 5 | 0 |
| Duplicate links suppressed | 13 | 13 |

Diagnostic precision among inspected accepted events was 28/28. Previously accepted charge-only and historical disclosures moved to rejected/ambiguous accounting context; they were not counted as lost operational events merely because the old manual diagnostic had called some plausible.

## Second unseen sample

Three companies and six documents produced 169 candidates and 64 accepted events. Thirty accepted events were inspected: 17 supported, 12 obvious false positives and one ambiguous, with no severe false positives. Diagnostic precision was 56.7%.

The failures were third-party context (4), generic risk (3), hypothetical risk (2), and one each for accounting/definition language, wrong context and malformed table text. This unseen result fails the technical-readiness threshold even though the specific historical/table problem improved.

## Decision

**NOT TECHNICALLY READY FOR HUMAN REVIEW.** Official Model 2 readiness remains **NOT READY**. The extractor should not be frozen as the candidate used for formal annotation comparison.

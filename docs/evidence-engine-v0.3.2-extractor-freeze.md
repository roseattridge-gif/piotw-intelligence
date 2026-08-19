# Evidence Engine 0.3.2 extractor freeze decision

Evidence Engine 0.3.2 is versioned and hashed for reproducibility, but it is **not frozen as the formal-review candidate**.

Reason: the five-document target passed and the 0.3.1 regression remained stable, but the second unseen sample produced 12 obvious false positives among 30 inspected accepted events. Freezing that extractor would overstate technical readiness.

The machine-readable results record hashes for the context rules, development-target config, taxonomy and parser, plus a combined extraction-engine hash. `release_frozen` is `false` and `git_commit` is `null` because no acceptable release commit was created.

The repaired `Evidence Engine 0.3 - Blinded Reviewer Pack v2` remains unchanged and uncontaminated. Formal review should not begin until a subsequent general context-hardening version passes another unseen development check.

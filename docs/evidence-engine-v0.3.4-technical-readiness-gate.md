# Evidence Engine 0.3.4 technical-readiness gate

Frozen before final unseen evaluation.

Mandatory conditions:

- model-backed new-unseen accepted-event precision at least 85% (90% preferred);
- zero severe false positives;
- zero attribution errors;
- semantic-invalidity false positives materially reduced;
- supported-event retention at least 85% on protected diagnostics;
- zero missed events on the six-document reviewed benchmark;
- 100% accepted-event evidence-span provenance;
- no material table, timing, entity, negation or duplicate regression;
- structured-output validity and fail-closed error handling demonstrated;
- the exact prompt, model and configuration frozen and hashed.

A deterministic/mock-only run cannot pass this gate. It may diagnose routing and plumbing, but `model_backed_unseen_evaluation_required_for_freeze=true`.

Passing status: `TECHNICALLY READY FOR BLINDED CROSS-REVIEW`. Otherwise: `NOT TECHNICALLY READY`.

Official Model 2 readiness remains `NOT READY` regardless.

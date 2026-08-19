# Evidence Engine 0.3.3 extractor freeze decision

Evidence Engine 0.3.3 is versioned and hashed for reproducibility but is **not frozen as the formal-review extractor**.

The technical gate failed because the new unseen sample achieved 43.3% diagnostic precision against an 85% minimum, included eleven obvious false positives, two severe false positives and one attribution error.

Accordingly:

- `release_frozen=false`;
- no release commit was created;
- the existing repaired blinded reviewer pack remains unchanged;
- no annotations were populated;
- no Model 2 work is authorized.

The current extractor and component hashes are recorded in `data/derived/evidence_engine_v0_3_3_results.json`. A later version must address semantic taxonomy entailment and source-span reliability and then face another genuinely unseen set before any freeze.

# Evidence Engine 0.3.4 Batch API execution

The execution unit is one frozen semantic candidate per `/v1/responses` Batch
request. Each JSONL row has a unique `custom_id`; results are reconciled by that
ID rather than output order. Candidate-level provider and parse failures are
preserved.

The Batch execution configuration is versioned separately from the scientific
semantic-verifier configuration. The current mechanical repair raises only the
output ceiling from 500 to 2,000 tokens. Scientific requests are stored under
`data/derived/evidence_engine_v0_3_4_batch/scientific_2000/`, keeping the prior
failed preflight immutable.

Before submission, the runner computes a conservative maximum Batch cost using
the request count, estimated input tokens, the full 2,000-token output ceiling,
and Batch pricing. Submission is blocked above USD 5.00.

The repository commit at execution time and all relevant configuration hashes
are recorded in the generated request manifest and preparation artefacts.

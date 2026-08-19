# PIOTW company intelligence contract v0.1

The canonical product object is `piotw-company-intelligence-v0.1`. It is the first runtime contract that represents Detect, Compare, Predict, Prescribe and Quantify together without requiring every engine to exist.

The contract deliberately separates:

- source evidence and evidence confidence;
- factual condition-candidate qualification results and established operational conditions;
- operational conditions and materiality;
- peer/history comparisons and comparability confidence;
- predictions and their model/horizon;
- interventions and their evidence/falsifiers;
- financial mechanisms and their assumptions/ranges.

Stage status is one of `AVAILABLE`, `WITHHELD`, `NOT_BUILT` or `INSUFFICIENT_EVIDENCE`. Unavailable stages cannot contain numerical results or recommendations.

`condition_qualifications[]` is an optional backward-compatible projection of the Operational Condition Qualification Engine. It explains what was observed, why a candidate might matter, which qualification tests failed, what remains unknown and what evidence would change the view. Only `QUALIFIED` results may create entries in `conditions[]`; insufficient candidates are never presented as established conditions.

Implementation: `piotw_intelligence/company_intelligence_v01.py`.

JSON schema: `config/piotw_company_intelligence_v0_1.schema.json`.

Generic frontend route: `/intelligence/[companyId]/value`.

Current source-backed development object: `piotw-web/data/company-intelligence-v01/travis-perkins.json`.

This contract is product plumbing, not a validated analytical method. Its purpose is to let engines be introduced or withheld independently while preserving one stable end-to-end interface and complete lineage.

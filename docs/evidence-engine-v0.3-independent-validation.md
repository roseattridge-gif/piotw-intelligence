# Evidence Engine 0.3 - independent validation

## Current decision

**NOT READY**

The 0.3 protocol and corpus are implemented, but independent human annotation has not yet occurred. No numerical, event, longitudinal, review-burden, or jobs-accuracy result is claimed. Scoring is deliberately blocked until human-first annotations are frozen.

## Prepared corpus

- 15 external US development companies
- 30 genuine historical SEC issuer filings
- two periods/documents per company
- annual, interim, and regulatory-results filings
- all tagged difficult, including dense/visual tables, adjusted/statutory ambiguity, restatements, acquisitions/disposals, segment changes, negative notation, repeated metrics, and multiple unit scales
- source HTML is retained as the authority; reviewer PDFs are mechanically rendered copies and are not substituted evidence

The corpus was selected without restructuring outcomes and is outside the frozen UK restructuring partitions.

## Blinded process

Human-first assignments expose only the source document and blank annotation schema. They do not expose extracted values, event labels, confidence, parser output, features, or predictions. The freeze command refuses empty, anonymous, untimestamped, or span-free annotations and records SHA-256 hashes. Only a verified frozen manifest permits comparison.

The separate PIOTW-first subset measures assisted review time and corrections; it does not become independent extraction gold.

## Reproduction

`make validate-evidence-engine-independent` verifies the 12 protected artefacts, development boundary, corpus shape, gold freeze, independent jobs labels, and review timings. Before human work is complete it exits cleanly with a machine-readable `pre_evaluation_blocked` result and **NOT READY**, rather than manufacturing zero-denominator accuracy.

## Scientific boundary

An AI system cannot independently validate its own output by adopting the role of a human reviewer. A real reviewer must complete and freeze the supplied annotation files. Repeated jobs lifecycle evidence also requires elapsed time across healthy collection runs. These are required observations, not engineering tasks that can honestly be simulated.

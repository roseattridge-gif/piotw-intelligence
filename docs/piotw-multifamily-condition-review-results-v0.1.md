# PIOTW Multi-Family Condition Policy Review v0.1 — Results

Status: **NOT_READY_INSUFFICIENT_REVIEW_SCOPE**

Method: development methodology review; not independent scientific validation

Cutoff: 19 August 2026 23:59:59 UTC

Frozen policy hash: `b5af92d2c913a39e0bd756c0a5e17549fc5f02ec3eaa0c5af871b7f8fa26e97d`

`scientific_gate_run`: `false`

## Result

The one preregistered run covered seven companies and four real evidence families. It produced 11 candidate decisions: eight qualified and three correctly withheld in the development source-first review. The protocol required 12 candidate decisions. Every other minimum-scope check passed, but the stopping rule forbids adding a convenient case after seeing results. Detect therefore does **not** advance to Compare.

The machine-readable record is `data/derived/piotw_multifamily_condition_review_v0_1_results.json`. It includes every observation, evidence reference, qualification test, failure and review classification.

## Company and evidence coverage

| Company | Estate periods | Leadership / organisation | Approved procurement | Careers | Candidate result |
|---|---:|---|---:|---:|---|
| Kingfisher | 3 | French operating-structure simplification | 0 | 0 | Estate expansion and organisational restructuring qualified |
| Howden Joinery | 4 | Board appointment (factual only) | 0 | 0 | Estate expansion qualified |
| Greggs | 3 | 0 | 0 | 0 | Estate reshaping and net expansion qualified |
| JD Wetherspoon | 4 | 0 | 0 | 0 | Estate reshaping and net contraction qualified |
| Kier Group | 0 | Risk/commercial reporting redesign | 6 resolved notices over 3 annual comparison periods | 0 | Organisation qualified; procurement acceleration withheld |
| Mears Group | 0 | 0 | 4 resolved notices over 3 annual comparison periods | 0 | Procurement acceleration withheld |
| Cloudflare | 0 | 0 | 0 | 2 | Hiring contraction withheld |

The estate histories use issuer-reported portfolio totals, not a complete site-level register. The procurement histories use exact legal names and Companies House identifiers in primary award notices; they remain a partial publication record, not a measure of total commercial demand.

## Source-first candidate review

All 11 factual observations used by candidates were supported by a primary-source span and retained provenance. All 11 entity scopes were judged correct for the stated record. Eight qualified decisions were judged reasonable development classifications; three conservative withholds were judged correct. There were no reviewed severe false positives, false negatives, unresolved contradictions or missing evidence pointers.

These counts are diagnostic, not accuracy claims. The two procurement cases remain explicitly ambiguous because sparse public-notice counts can change with buyer publication behaviour and do not represent all awards or revenue.

## Policy assessment

| Family policy | Assessment | Reason |
|---|---|---|
| Estate expansion / contraction / reshaping | **KEEP FOR NOW** | Multi-period totals, denominator and direction behaved transparently across four issuers. Portfolio-definition consistency and site-level resolution remain limitations. |
| Leadership / organisational restructuring | **NEEDS MORE DATA** | The rule correctly distinguished operating-structure changes from a routine Board appointment, but two qualifying events are too few to demonstrate generalisation. |
| Procurement activity acceleration / deceleration | **SPLIT INTO SOURCE-SPECIFIC POLICY** | Exact entity resolution worked, but notice frequency is source- and buyer-dependent. Annual comparison periods were shallow and both candidates were correctly withheld. Any future policy must distinguish award/notice types and publication completeness. |
| Careers expansion / contraction | **NEEDS MORE DATA** | The two-snapshot Cloudflare movement remained insufficient for persistence and magnitude. |

No thresholds or frozen family policy were changed after the run.

## Cross-family corroboration and contradiction

No real record in this set established an explicit independent relationship to another family's candidate. Shared ontology dimensions were correctly ignored. Kingfisher's organisational redesign was not treated as evidence for its estate expansion; Kier's procurement notices were not treated as corroboration for its risk-structure redesign. No source-backed contradictions were present.

The engine's explicit support, contradiction and derivative-duplicate mechanics remain covered by regression tests, but genuine real-world cross-family corroboration is not yet demonstrated.

## Readiness decision

Detect is **not yet trustworthy enough to move to Compare**. The narrow blocker is not factual extraction or entity resolution in this sample. It is an underpowered, uneven policy review: 11 decisions missed the preregistered 12-decision minimum, leadership has only two substantive condition cases, and procurement needs a source-specific completeness policy before notice-count changes can qualify.

The next P0 is a preregistered extension using new, development-safe cases selected before evaluation: at least one further direct organisational-change case and deeper, source-homogeneous procurement histories. Re-run the same unchanged policy once the minimum scope is met. Do not build a score or percentile.

## Primary sources

- Kingfisher annual reports/results: `kingfisher.com`
- Howden Joinery annual reports/results: `howdenjoinerygroupplc.com`
- Greggs annual reports: `assets.greggs.com`
- JD Wetherspoon annual report: `investors.jdwetherspoon.com`
- Kier annual reports: `kier.co.uk`
- UK Find a Tender and Contracts Finder award notices: `find-tender.service.gov.uk`, `contractsfinder.service.gov.uk`
- Cloudflare approved careers collector snapshot: `cloudflare.com/careers/jobs`

# PIOTW Procurement Source Feasibility v1

Status: development feasibility and collection-only proof of concept.

## Sources assessed

| Source | API/bulk | History and timestamps | Award detail | Access/cost | Assessment |
|---|---|---|---|---|---|
| Find a Tender | public OCDS release-package API and XML downloads | strong dated archive; release/record IDs | buyer, suppliers, value, status, dates and categories where supplied | public, no paid dependency | selected primary MVP |
| Contracts Finder | OCDS search/record/release APIs and dated daily CSV | strong historic daily retrieval | buyer/supplier and award value, with varying completeness | public, no paid dependency | complementary next adapter |
| data.gov.uk procurement archives | downloadable datasets/API catalogue | strong for published archive files | source-dependent | public | fallback/backfill route |

Find a Tender is selected because its official OCDS interface has stable release/process identifiers, publication-date filters and structured award parties. This is a collection decision, not evidence that public awards predict company growth.

## Adapter

`pipelines/procurement/find_a_tender.py` parses OCDS releases into immutable raw records containing notice/release ID, publication date, buyer, supplier, value/currency, category, description, status, contract period, source URL, raw payload and hash. Parsing is deterministic and idempotent.

A read-only live check against the official API retrieved five releases dated 1 August 2026. The adapter produced five immutable records; three contained named suppliers and every record retained a valid SHA-256 content hash. The bounded raw sample is preserved at `data/collection_samples/procurement/find_a_tender_2026-08-01_limit5.json`.

Supplier entity resolution preserves the raw and normalized name. Only an unambiguous normalized exact alias can attach automatically; everything else remains unresolved with a manual-review flag. Corporate group/subsidiary resolution remains the largest practical data-quality issue.

## Backfill and cadence

Historical point-in-time reconstruction is **strong** for notices retained by the official services, though later corrections/releases must be versioned. Proposed cadence is daily. Store all releases for an OCID rather than overwriting earlier states.

## Limitations

- Supplier names may identify subsidiaries, consortia or trading names rather than listed parents.
- Publication does not prove delivery, revenue recognition, profitability or incrementality.
- Award values may be ceilings, multi-supplier totals or absent.
- Losses are usually not observable merely because another supplier won.
- Coverage is structurally biased toward public procurement.

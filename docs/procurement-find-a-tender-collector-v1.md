# Find a Tender persisted collector v1

0.3.6 stability note (18 August 2026): the first daily persisted run parsed 158 records into 111 stable release streams and 157 immutable versions. Eighty-six named suppliers remain in the review queue and zero aliases are approved. Collection works, but one run and unresolved entities are not sufficient for company-level longitudinal features.

The collector stores official OCDS releases daily without assigning predictive meaning. A stable notice/supplier key identifies a fact stream; the raw payload hash identifies its version. An unchanged re-fetch is idempotent. A changed payload creates a new immutable version and keeps the earlier version.

Persisted fields include publication and contract dates, buyer, raw supplier name, value/currency, category, status, source URL, retrieval time, collector version, raw OCDS JSON and SHA-256 content hash.

Supplier matching fails closed. Only a unique approved exact alias may resolve automatically. All other named suppliers enter the manual review queue; missing suppliers remain missing rather than fabricated. Daily execution is provided by `scripts/collect_find_a_tender_daily_v1.py`.

This is a collection substrate, not a procurement feature or growth signal. Contracts Finder should be considered only after several healthy daily Find a Tender runs demonstrate stable versioning and manageable entity-review burden.

## First persisted live run

The 18 August 2026 official API collection returned 158 supplier/award records. They resolved to 111 stable notice/supplier streams and 157 immutable payload versions; multiple updates to a stream inside the source material were retained rather than overwritten. Eighty-six streams named suppliers and all 86 entered the unresolved manual queue because no approved canonical alias registry was supplied. There was one persisted collection run. No supplier was attached to a listed company automatically.

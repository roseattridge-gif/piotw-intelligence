# PIOTW Collection Cadence and Backfill v1

> **CANDIDATE PRODUCT ONTOLOGY — NOT YET EMPIRICALLY VALIDATED**

## Cadence principle

Cadence is a function of how often the source changes, its early-warning value, access cost, source reliability and historical reproducibility. A faster poll is useful only if collection health can be distinguished from company change.

| Source family | Proposed cadence | Backfill | Failure control | Priority |
|---|---|---|---|---|
| issuer disclosures | event-driven feed plus daily check | strong | publication ID/hash deduplication | existing core |
| careers/ATS | every two days | weak | successful-fetch requirement, site-health status, repeated-miss closure | build now |
| contracts/procurement | daily | strong | notice ID/version and award-status history | build now |
| regulatory operating notices | daily | strong | authority/source ID and correction history | build now |
| physical footprint/capacity | weekly | partial | application/permit lifecycle and jurisdiction health | build next |
| company newsroom | daily | partial | canonical URL/hash and issuer boundary | build next |

## Jobs assessment

The present real baseline captured 2,540 jobs across 11 successful companies on Greenhouse, Lever and Ashby; one company failed collection. It proves multi-platform discovery, not longitudinal reliability. It cannot yet establish true vacancy closure, velocity or historical change.

Before use beyond observation storage, jobs need:

- repeated scheduled snapshots;
- platform and company source-health state;
- confirmation over multiple successful absences before closure;
- repost/linkage rules;
- stable function, seniority and location classification;
- explicit coverage gaps and no imputation of missing pages.

## Ranked build plan

1. **Now:** make careers snapshots genuinely longitudinal; extend event-driven issuer announcements; add UK public procurement and high-value regulatory operating notices.
2. **Next:** physical footprint/permit adapters and company newsroom feeds where history can be retained.
3. **Later:** leadership, supplier, web-traffic, employee-review and other noisier/licensed sources only after access, provenance and reproducibility studies.

## Scale controls

Collectors share one evidence contract, cache immutable artefacts, avoid downloading unchanged content, record retries and cost, and expose source-level health. Backfill quality is stored alongside coverage so a company with a rich archive is not silently compared with one having only a current snapshot.


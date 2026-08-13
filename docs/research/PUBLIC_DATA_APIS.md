# Public data/API plan (v0.2)

Status: implemented locally on 13 August 2026. No paid service is required. “Free” below means no usage fee discovered; account creation, an API key, rate limits and provider terms may still apply.

## What we should measure

Raw counts are not model inputs on their own. Each collector creates dated observations; features are calculated against the same company’s earlier baseline and, where possible, a sector peer baseline.

| Signal family | Candidate metrics | Expected lead/lag | Initial model share |
|---|---|---:|---:|
| Workforce demand | Open-role count; 30/90-day net openings; hiring velocity; seniority; operations/quality/data/change mix; new sites/geographies; replacement-language rate | 1–4 quarters | 15% pressure / 22% expansion |
| Leadership | New COO/CFO/CTO/transformation roles; director appointments/resignations; leadership churn | 1–4 quarters | 12% / 12% |
| Procurement/demand | Contract awards, award value, buyer concentration, tender frequency, wins/losses where observable | 1–6 quarters | 9% / 12% |
| Corporate activity | Filing frequency/type, charges, acquisitions/disposals, restructurings, capital raises | 1–6 quarters | 7% / 6% |
| Operational disclosure | Capacity constraints, backlog, lead times, quality, outages, exceptional costs and restructuring language in official releases | 0–3 quarters | 16% / 10% |
| Capacity footprint | New/closed facilities, permits, leases, footprint language, plant and supply-chain roles | 2–8 quarters | 10% / 16% |
| Product/quality | Recalls, regulator actions, certifications, quality/safety job mix, warranty language | 0–4 quarters | 12% / 8% |
| Web attention | Careers/IR page change rate and search interest, used only as corroboration | 0–2 quarters | 7% / 6% |
| Sector context | Vacancies, output, orders, prices, insolvencies and confidence series | contemporaneous | 7% / 4% |
| Financial baseline | Revenue/profit/cash/debt direction known at the cutoff | contemporaneous | 5% / 4% |

These are family-level starting weights, not learned truth. Within a family, an observation is still multiplied by source reliability, strength, materiality, recency and independence. We will freeze these priors before evaluation, then use walk-forward tests to learn whether a feature deserves weight. Missing data must reduce confidence, not create a neutral or positive signal.

## ATS and careers sources

ATS means applicant tracking system. The names in the question were probably **Workday** and/or **Workable**; “Workforce” is a generic HR term and is also used in some product names.

| Platform | Public-data route | Access | Built now | Treatment |
|---|---|---|---|---|
| Greenhouse | `GET /v1/boards/{token}/jobs?content=true` | Public, no key | Yes | Preferred |
| Lever | `GET /v0/postings/{site}?mode=json` | Public, no key | Yes, including EU host | Preferred |
| Ashby | `GET /posting-api/job-board/{board}` | Public, no key | Yes | Preferred |
| SmartRecruiters | company postings endpoint | Public postings | Yes | Preferred, validate tenant identifier |
| Recruitee | careers-site offers feed | Public careers feed | Yes | Preferred when employer exposes it |
| Workday | External careers pages; no general documented public job-board API | Page access varies | Detection only | Parse permitted public `JobPosting` structured data; do not call undocumented tenant endpoints by default |
| Workable | Customer API uses account credentials | Authenticated | Detection only | Public structured page/RSS only when exposed |
| Teamtailor | Public API requires API key | Authenticated | Detection only | Add only with employer-authorised key |
| iCIMS, Taleo, SAP SuccessFactors, Personio | Varies by tenant | Usually page/feed or authenticated | Detection only | Structured-data/feed fallback; per-tenant terms and robots check |

Official references: [Greenhouse Job Board API](https://developers.greenhouse.io/job-board.html), [Lever Postings API](https://github.com/lever/postings-api), [Ashby public job posting API](https://developers.ashbyhq.com/docs/public-job-posting-api), [SmartRecruiters Posting API](https://developers.smartrecruiters.com/docs/endpoints), [Recruitee API overview](https://support.recruitee.com/en/articles/1066282-api-documentation), [Workable API](https://workable.readme.io/reference/jobs), [Teamtailor API](https://docs.teamtailor.com/).

### Why snapshots matter

Most public job APIs expose current vacancies, not a historical archive. `scripts/collect_careers.py` therefore saves each run to SQLite, preserving first seen, last seen and no-longer-observed dates. From that we can derive:

- opening and disappearance rates rather than one noisy count;
- function and seniority mix shifts;
- new location/site signals;
- persistent hard-to-fill roles;
- demand acceleration relative to the company’s own baseline.

Disappearance is not labelled “filled” unless another source proves it. Reposted and renamed roles need fuzzy deduplication in the next research iteration.

## Other useful official APIs

| Source | Useful observations | Cost/access | Built now | Reliability role |
|---|---|---|---|---|
| Companies House | Company profile, filing history, officers; later charges/PSC | No usage fee; free account/API key; 600 requests per five minutes | Profile, filings, officers | High for the fact filed, not for commercial interpretation |
| ONS beta API | Sector vacancies, output, orders, prices, labour and business context | Open, no key; beta | Dataset catalogue/latest version | High sector baseline |
| Contracts Finder OCDS | Published UK opportunities and awards, suppliers and award values | Public read endpoints | Published-notice date window | High for published procurement; incomplete for total company demand |
| SEC EDGAR | Submissions and XBRL facts for US-listed issuers/ADRs | Open, no key; descriptive contact user-agent required | Submissions and company facts | High official filing source |
| Company investor-relations pages/RSS | Results, trading updates, acquisitions, capacity and restructuring releases | Public page/feed; no universal API | Existing document pipeline; feed adapter next | Highest first-party narrative source |
| Regulatory/product databases | Recalls, enforcement, safety and environmental events | Varies by regulator | Not yet | High when identity mapping is strong |
| GDELT/news aggregators | Mentions and discovery of local events | Free/open, coverage/noise varies | Not yet | Discovery only; confirm against original source |
| Search/social/job aggregators | Attention and discovery | Terms and historical access vary | Not in MVP | Low weight; never substitute for source evidence |

Official references: [Companies House getting started](https://developer.company-information.service.gov.uk/get-started), [Companies House limits](https://developer.company-information.service.gov.uk/developer-guidelines), [ONS API](https://developer.ons.gov.uk/), [Contracts Finder API](https://www.contractsfinder.service.gov.uk/apidocumentation), [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).

## Guardrails

1. Use documented APIs and feeds first. Public visibility is not automatically permission for unrestricted automated collection.
2. Respect robots instructions, provider terms, rate limits and `Retry-After`; keep request volumes deliberately low.
3. Store URL, provider identifier, retrieval time and raw content hash for every observation.
4. Do not collect applicant or employee personal data. Published role and officer-level public records are the scope.
5. Never infer causation from one source. A signal becomes stronger through independent corroboration.
6. Preserve point-in-time availability so later information cannot leak into a retrospective prediction.
7. Treat API/provider failure as missingness and reduce confidence.

## Implementation map

- `pipelines/careers/discovery.py`: recognises common ATS URLs and states whether a documented public API exists.
- `pipelines/careers/adapters.py`: normalises five public ATS feeds into one `JobPosting` schema.
- `pipelines/careers/jsonld.py`: extracts schema.org `JobPosting` blocks from HTML already retrieved under an allowed page policy.
- `pipelines/careers/storage.py`: point-in-time SQLite snapshots and closure observations.
- `pipelines/public_data/clients.py`: Companies House, ONS, Contracts Finder and SEC clients.
- `scripts/collect_careers.py`: config-driven collection command.

The next honest validation step is to identify the careers host and tenant identifier for every pilot company, run the first snapshot, and retain repeated snapshots prospectively. Historical job-posting claims cannot be reconstructed reliably from today’s APIs alone.

For the current three-company pilot, the initial discovery found fragmented Chemring business-unit links, a first-party Vesuvius careers page, and a Bodycote careers site consistent with Teamtailor. None has therefore been force-fitted into one of the five no-key adapters. They are recorded, disabled, in `config/career_sources.json` pending a robots/terms-aware page collector and per-business Chemring mapping.

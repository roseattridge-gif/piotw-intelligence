# PIOTW current-state audit

## Scope and frozen-state confirmation

This is a read-only analytical audit of commit `eac7499a8ea659e126036675f773471a3d3451f6`, plus these requested documentation files. No model, prediction, cohort, evidence, feature, validation protocol, outcome protocol, or frozen artifact was modified. No new outcome research or adjudication was performed.

The frozen model specification hash is `213d13648f4f`. The frozen dataset has:

- 291 total manifest occasions;
- 289 immutable predictions;
- two documented exclusions, both Dowlais occasions (2020 and 2022). They use the frozen `uninterpretable_entity_at_cutoff` rule: Dowlais was incorporated and listed only after those cutoffs, so the prediction entity/target was not meaningful at those dates.

## What was actually collected and extracted

### Raw source material represented in final evidence

Every predicted occasion has one final evidence row. Classification by final source title is:

| Source type | Final evidence rows |
|---|---:|
| Annual report, annual report and accounts, or annual financial statements | 285 |
| Final/full-year results announcement | 3 |
| Prospectus | 1 |
| **Total** | **289** |

There are no interim reports in the final 289-row evidence table. There is no systematic frozen-v2 collection of job data, news, procurement, planning, LinkedIn, employee reviews, patents, web traffic, or supplier data.

The source-index status across all 291 manifest occasions is:

| Source-index status | Occasions |
|---|---:|
| Preserved | 273 |
| Retrieval failed | 16 |
| Parse failed | 2 |
| **Total** | **291** |

For the 289 predicted occasions, the source-index count is 273 preserved, 14 retrieval failed, and two parse failed. The two excluded occasions account for the remaining retrieval failures.

There is an important second preservation measure in the final evidence table:

| Final evidence preservation status | Rows |
|---|---:|
| `preserved` with linked raw file/hash | 81 |
| `unavailable_documented` fallback evidence row | 208 |
| **Total** | **289** |

These figures are not contradictory definitions of the same thing. The source index says a collector preserved bytes for 273 occasions, but only 81 final evidence rows carry the raw path/hash link. The remaining 208 were built through the manual web/fallback review route and are marked `unavailable_documented`, even when the source index separately records preserved material. This disconnect weakens the audit chain and should not be described as 273 fully linked prediction evidence packages.

The 208 fallback rows use `web-primary-extract-manual-1`; 81 linked rows use `pypdf-6.16.0+manual-1`.

### Structured automatic fields

The collection/index stage can record:

- ticker and report year;
- source URL;
- collection status and failure reason;
- raw file path and SHA-256;
- extracted-text path and SHA-256;
- PDF page count;
- candidate report approval/authorization dates found by regex;
- retrieval timestamp.

The final evidence table records:

- evidence and occasion IDs;
- company and ticker;
- `available_at` date;
- availability basis and the evidence supporting that date;
- source title and URL;
- retrieval time;
- raw path/hash when linked;
- preservation and parser status;
- source page/location references;
- narrative observation;
- evidence direction (all frozen rows are `mixed`);
- already-announced activity to exclude from a future outcome;
- canonical extraction hash;
- review status.

The feature table records the four scores, ordered evidence IDs, and feature review status.

### What was manually extracted and scored

A human reviewer had to provide or approve:

- source substitutions/fallbacks where automated collection was insufficient;
- publication/availability date basis and explanatory evidence;
- the relevant pages;
- the narrative evidence observation;
- already-announced restructuring or related action to exclude;
- reviewer note/status;
- `pressure_language`;
- `margin_pressure`;
- `cash_pressure`;
- `contrary_strength`;
- exclusion recommendation where evidence was insufficient.

The four numeric fields allow `0.00` through `1.00` in `0.05` increments. The full manual rubric is reproduced in `docs/piotw-rules-1.0.0-signal-inventory.md`.

The automated review-packet generator searched PDF text for candidate excerpts around terms associated with pressure, margin, cash, and contrary evidence. It retained a limited number of contextual snippets per category. That was navigation assistance only: it did not calculate any of the four scores.

## What “evidence complete” means here

The coverage-queue code calls an occasion complete when its ID appears in both `evidence.csv` and `features.csv`. It does not prove that:

- every eligible disclosure was found;
- multiple sources were reviewed;
- the selected report was truly the latest eligible disclosure;
- raw bytes are linked to the final evidence row;
- every relevant page was extracted;
- a second reviewer agreed;
- external evidence categories were covered.

By that narrow implemented definition, all 289 predicted occasions are complete and none is labelled partial. The two remaining manifest occasions are excluded.

Every prediction has all four inputs. If a feature is missing, outside 0–1, or the feature keys do not match exactly, the model errors; it does not fill zero or reduce the probability. Insufficient evidence is intended to exclude the occasion. Therefore missing evidence does not numerically lower current predictions—it prevents a prediction—but this can create selection bias.

The repository does not measure systematic coverage quality by company. It shows 90 companies with three prediction occasions, nine with two, and one with one. Every occasion has one evidence row and the same confidence, but source type, preservation linkage, cited-page breadth, disclosure detail, and accessibility vary substantially. Some companies therefore have richer underlying evidence despite identical record counts and confidence.

## Evidence types: actual frozen-model status

“Direct” means the source or numeric feature is explicitly part of the frozen prediction path. “Indirect” means it can influence a manual composite score but is not a separate model input.

| Evidence discussed | Status | Actual implementation finding |
|---|---|---|
| Job vacancies | NOT COLLECTED | No frozen-v2 job evidence feeds the 289 predictions; collector/prototype code elsewhere is disconnected. |
| Careers-page changes | COLLECTED BUT NOT USED | Limited page-snapshot work exists elsewhere in the repository, not in the v2 prediction path. |
| Hiring acceleration/deceleration | NOT COLLECTED | No frozen-v2 hiring time series or feature. |
| Companies House filings | USED INDIRECTLY | Ten report URLs use Companies House document delivery, but filing events are not a feature. |
| Annual reports | USED DIRECTLY | 285 of 289 final evidence sources. |
| Interim reports | NOT COLLECTED | None in the final v2 evidence set. |
| RNS/regulatory announcements | USED DIRECTLY | Three final/full-year results announcements are evidence; this is not a systematic RNS feed. |
| Contracts/procurement awards | NOT COLLECTED | Collector scaffolding elsewhere is not used for v2. |
| Find a Tender | NOT COLLECTED | No frozen-v2 evidence or feature. |
| Planning applications | NOT COLLECTED | No frozen-v2 evidence or feature. |
| Press releases | NOT COLLECTED | No systematic general press-release collection; results announcements are classified above as regulatory/issuer results. |
| Management changes | UNKNOWN | No structured collection or feature; a change could appear incidentally in a reviewer’s report summary. |
| LinkedIn | NOT COLLECTED | No frozen-v2 evidence or feature. |
| Employee reviews | NOT COLLECTED | No frozen-v2 evidence or feature. |
| Glassdoor | NOT COLLECTED | No frozen-v2 evidence or feature. |
| News | NOT COLLECTED | No frozen-v2 news evidence or feature. |
| Patents | NOT COLLECTED | No frozen-v2 evidence or feature. |
| Web traffic | NOT COLLECTED | No frozen-v2 evidence or feature. |
| Supplier signals | NOT COLLECTED | No frozen-v2 evidence or feature. |
| Capex | USED INDIRECTLY | Can inform a manual cash/contrary judgment if mentioned, but is not separately extracted or weighted. |
| Cash | USED DIRECTLY | Manually converted into `cash_pressure`, one of four inputs. |
| Margins | USED DIRECTLY | Manually converted into `margin_pressure`, one of four inputs. |
| Restructuring provisions | USED INDIRECTLY | Can influence pressure/cash judgment and exclusion notes; no separate input. |
| Exceptional costs | USED INDIRECTLY | Can influence the manual composites; no separate input. |
| Impairment language | USED INDIRECTLY | Can influence pressure/margin judgment; no separate input. |
| Cost-reduction language | USED INDIRECTLY | Explicitly relevant to `pressure_language`, but mediated by a manual composite score rather than automatically counted. |
| Transformation language | USED INDIRECTLY | May influence pressure or contrary judgment; no separate transformation feature. |
| Supply-chain language | USED INDIRECTLY | Explicitly relevant to the pressure rubric; no separate feature. |

## Automated versus manual

### Automated

- Build and hash the candidate universe and cohort manifests.
- Choose the target report year pattern and attempt known/registered URLs.
- Download files, check PDF signatures, hash bytes, and extract page text.
- Find candidate approval dates and keyword-led review excerpts.
- Validate cutoff dates, required fields, evidence IDs, score ranges, and 0.05 increments.
- Create canonical extraction and prediction snapshot hashes.
- Join evidence and features to manifest occasions.
- Calculate the four contributions, raw score, and probability.
- Create portable JSON predictions and immutable SQLite rows.
- Reject updates/deletes to frozen prediction rows.
- Run reproducibility, no-outcome, and integrity tests.

### Manual

- Resolve failed/incomplete source collection and choose fallback evidence.
- Judge whether a source was eligible and available by the cutoff.
- Read the source and identify relevant pages.
- Write the evidence summary and contradictory evidence.
- Identify already-announced programmes that cannot be future outcomes.
- Assign all four feature scores.
- Recommend evidence-quality exclusions.

All four predictive inputs—and therefore all 1,156 frozen input values—are manually scored. Once those values exist, the probability calculation and freezing are fully automated. The repository does not record time in a way that supports a credible percentage of total labour. On prediction dependence, the accurate split is **100% manual input generation; 100% automated arithmetic/validation/registration**. Overall this is a hybrid leaning toward a manually coded research process, not an automated intelligence engine.

## Actual current architecture

| Stage | What enters | What happens | What comes out | Manual or automatic? |
|---|---|---|---|---|
| Candidate manifest | Frozen issuer universe and cutoff policy | Stable occasion IDs, company/ticker/cutoff, partition, and hashes are created | 291 occasion manifests | Automatic after universe decisions |
| Source collection | Ticker/report year, official registry and fallback URL patterns | Attempts PDF download, signature check, hashing, text extraction, page count, candidate date detection | Source index, raw PDFs/text where successful | Automatic, with manual registry/source decisions |
| Fallback handling | Failed/partial collection and browser-accessible issuer material | Reviewer records source identity, availability evidence, pages, and observation | Manual web review rows | Manual |
| Evidence review | Selected disclosure and keyword excerpts | Reviewer reads source as a whole, records support/contradiction and already-announced activity | One evidence record per predicted occasion | Manual, aided by automatic excerpts |
| Feature scoring | Evidence review and frozen rubric | Reviewer assigns four 0–1 scores | One four-feature vector | Manual |
| Evidence build | Review rows, manifests, raw/index files | Validates fields/dates/grid; creates hashes and normalized CSVs | `evidence.csv`, `features.csv` | Automatic |
| Rules model | Four numbers | Applies fixed weighted log-odds formula and sigmoid | Probability and contributions | Automatic |
| Frozen registry | Probability, features, evidence IDs/hashes, model hash | Enforces uniqueness and database immutability; exports JSON | 289 frozen predictions | Automatic |
| Outcome/evaluation | Not entered for v2 | Paused; no v2 outcome adjudication in this audit | No v2 result | Not performed |

There is no entity-resolution engine or event-resolution engine operating inside this v2 path. Stable manifest IDs and a manual already-announced exclusion provide limited identity/event handling, but should not be described as full resolution.

## Built-state comparison with the broader vision

### BUILT AND WORKING

- Frozen v2 candidate manifests and deterministic hashes.
- A report collector, source registry/index, PDF checks, text extraction, and review-packet generation.
- A structured evidence/features dataset for 289 occasions.
- The four-input Rules 1.0.0 restructuring predictor.
- Immutable SQLite prediction registry and portable JSON exports.
- Fail-closed no-outcome execution and integrity/reproducibility tests.
- Earlier v1 outcome/evaluation machinery and comparator implementations, separate from unresolved v2.

### PARTIALLY BUILT

- **Collectors:** code exists for additional sources, but the frozen v2 experiment principally uses issuer reports and does not orchestrate the wider feeds.
- **Evidence store:** structured CSVs, source index, hashes, and SQLite exist, but final raw-file linkage is complete for only 81 evidence rows.
- **Entity resolution:** generic primitives and stable IDs exist elsewhere; v2 relies mainly on the frozen manifest rather than a live resolver.
- **Event resolution:** target definitions, deduplication ideas, and earlier outcome machinery exist; v2 event outcomes remain untouched.
- **Feature engine:** validation and deterministic calculation exist, but feature production is manual rather than an automatic engine.
- **Backtesting:** small v1 work and v2-ready evaluation code exist; broad v2 backtesting has not occurred.
- **Dashboard:** a React interface exists for earlier v1/pilot/Bodycote material, but it does not present the 289 frozen v2 predictions as the current prototype view.
- **Multi-source intelligence:** collectors/demonstrations exist in fragments, but they are not connected to Rules 1.0.0.

### SPECIFIED BUT NOT BUILT

- A production Pressure model combining a broad signal set.
- An Expansion model.
- The broader signal catalogue operating as a live feature system.
- Production-grade peer comparisons and sector indexes.
- Systematic multi-source evidence coverage and source-quality-aware confidence.
- A live founder-facing product workflow over the frozen-v2 architecture.

### NOT YET ATTEMPTED AS AN OPERATIONAL SYSTEM

- Continuous live monitoring of the full cohort across all proposed sources.
- Production alerting/orchestration and ongoing entity/event maintenance.
- Systematic use of LinkedIn, employee reviews, Glassdoor, patents, web traffic, supplier signals, planning applications, and Find a Tender in predictions.

## Pressure/Expansion relationship

Rules 1.0.0 does not calculate Pressure or Expansion. It calculates only a 365-day restructuring-announcement probability from four manual scores.

Operational-pressure and expansion/transformation concepts exist in separate specifications and demonstration code. They are not upstream features in the frozen 289 predictions. The current restructuring work is best understood as a narrow first experiment relevant to one possible future Pressure dimension—not a direct Pressure score and not a two-sided Pressure/Expansion model.

## What is concerning, without proposing fixes

1. **No documented derivation for the main parameters.** The 12% prior, four weights, 0.05 grid, rubric boundaries, and sigmoid calibration are frozen assumptions, not learned or empirically calibrated values.
2. **Single-reviewer subjectivity.** Every predictive input is a manual ordinal score with no independent duplicate review or recorded agreement testing.
3. **Overlap and possible double-counting.** Operational-pressure language can include margin/cash problems, while separate margin and cash features count them again. Contrary strength can then encode their inverse.
4. **Target-adjacent language.** The pressure rubric explicitly permits pre-cutoff restructuring activity that is not itself the future outcome. That may be a useful precursor, but distinguishing continuation from a new programme is subjective and creates leakage risk if applied inconsistently.
5. **Narrow completeness definition.** “Complete” means one evidence row plus one feature row, not comprehensive pre-cutoff evidence.
6. **Preservation-link disconnect.** The source index records 273 preserved documents, while only 81 final evidence rows link raw paths/hashes; 208 final rows say `unavailable_documented`.
7. **Coverage confidence is not informative.** Every prediction receives 0.48 despite substantial differences in source preservation, page breadth, source type, and fallback handling.
8. **Availability-date risk.** Many rows use board approval or document authorization as availability evidence. Those dates do not always prove public release on that date, creating a potential cutoff-control weakness.
9. **Potentially stale disclosure selection.** The automated pattern targets reports for 2019, 2021, and 2023 for cutoffs in 2020, 2022, and 2024. Later eligible interim/trading disclosures are not systematically incorporated, despite documentation referring to the latest eligible disclosure set.
10. **Evidence availability bias.** Missing inputs exclude an occasion rather than lowering confidence or being modelled. Easy-to-retrieve, detailed issuers may therefore be represented differently from difficult ones.
11. **Manual summaries replace bounded raw extraction in places.** The `observation` field is a reviewer-authored synthesis, not consistently a verbatim extract. The disclosure-language comparator searches that summary in the implemented evaluation path rather than the whole source text.
12. **Broad contrary composite.** Growth, orders, margins, cash, liquidity, recovery, and completed interventions are collapsed into one subtractive score, allowing one subjective field to offset several risk dimensions.
13. **Documentation/product impression exceeds current model scope.** The repository discusses 54 signals, Pressure/Expansion, multiple collectors, and a dashboard. None of that changes the four-feature frozen v2 probability. The current UI also does not expose the 289 predictions.
14. **Third-party archive dependence.** A substantial number of report URLs use AnnualReports.com or other archives. The document may be an issuer report, but provenance and availability controls are not equivalent to an issuer-hosted publication.
15. **Validation remains limited.** The main broad 289-prediction set has not been outcome-tested. The earlier 20-occasion work is too small to establish calibration or general performance, and its documented formal gate was not a clean pass.

## What the prototype has successfully achieved

The strongest achievement is not proof of predictive accuracy. It is an auditable experiment boundary: fixed company-date occasions, pre-cutoff evidence records, explicit manual inputs, deterministic mathematics, model/evidence hashes, and immutable predictions frozen before broad outcome resolution. That makes honest later testing possible and prevents retrospective rewriting of the forecast.

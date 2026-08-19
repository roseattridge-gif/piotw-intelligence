# Evidence Engine 0.3.5 development proposal

Status: proposal only. No 0.3.5 extractor has been implemented or evaluated.

## Objective

Improve factual event recognition across general failure classes revealed by the preserved 0.3.4 failure, while retaining exact provenance and supported-event recall. This is not permission to tune repeatedly on the failed scientific gate.

## Proposed development changes

| Failure class | Proposed general change | Layer | Regression risk | Required tests |
| --- | --- | --- | --- | --- |
| Hypothetical risk accepted as actual | Add clause-level risk construction detection and require a realised occurrence/effect for current events | deterministic candidate/context | May reject sentences combining realised and future effects | pure risk; realised event plus future risk; “may” used as month/name/non-modal |
| Legal/accounting definition accepted | Identify litigation enumerations, definitions and accounting-policy constructions; reject unless a separate factual action is asserted | deterministic structural context | Could hide real events disclosed in notes | definition-only; definition followed by quantified current programme; litigation arising from named current programme |
| Industry subject attributed to company | Resolve grammatical/semantic subject before inheriting “we/our” from neighbouring context | entity/context | Could reject company exposure described after macro subject | global-only; global plus explicit company effect; segment and supplier cases |
| Heading accepted as evidence | Require accepted pointer to contain a complete factual proposition; headings may locate but cannot support alone | contract/local validator | Could reject terse but valid table labels | heading-only; heading plus adjacent statement; quantified table row with headers |
| Growth taxonomy polarity | Retire lexical `growth_language` as a factual event candidate in 0.3.5; create objective revenue/demand/order direction observations | taxonomy/design | Breaks backward feature names; requires migration alias | revenue up/down; expense up; FX impact; forecast assumption; demand/order/backlog direction |
| Pricing pressure gap | Add `pricing_pressure` observation/event distinct from margin deterioration | taxonomy + semantic | Overlap with inflation and competitive pricing | realised pricing pressure; hypothetical pricing risk; margin consequence present/absent |
| Backlog decline gap | Extract backlog amount and change as objective observations; interpret demand only when scope/context supports it | numeric/table extraction | Backlog changes can reflect delivery, cancellation or FX | current/prior header alignment; acquisition/FX changes; segment scope |
| Malformed PDF join | Add span structural-quality flags and sentence/table segmentation before event candidature | source processing | Over-aggressive fragmentation | multi-column joins; table/narrative boundary; legitimate long sentence |

## Semantic-contract clarifications

- “Actual/current” requires an asserted realised condition, action or effect—not merely exposure, possibility or a metric’s definition.
- The accepted evidence span must itself entail the event; surrounding context may disambiguate but cannot substitute for evidence.
- Subject, affected scope and actor must be separated. Paying a charge associated with dealers does not automatically mean the company itself restructured.
- Planned and implemented events remain distinct.
- Semantic output must support polarity for directional observations where the taxonomy requires it.

No change to model choice is proposed at this design stage. Any later model/prompt change must be versioned and tested on development data before one genuinely fresh frozen gate.

## Development process

1. Freeze this proposal and the contamination register.
2. Build deterministic structural/context changes behind namespace `evidence_engine_v0_3_5`.
3. Add the 11 failure cases and supported counterexamples as development regressions.
4. Add fresh synthetic and real development cases for every failure class.
5. Measure precision, supported retention and provenance on development data only.
6. Pre-register a new validation protocol and choose fresh companies/documents not present in any 0.3.x development or inspection set.
7. Freeze candidates, annotations, thresholds and hashes before provider execution.
8. Run once; preserve pass or failure.

## Fresh validation requirements

- at least 5–8 genuinely unused companies and 10–16 difficult reports;
- deliberate coverage of risk factors, legal notes, accounting definitions, multi-column text, tables and mixed current/forward language;
- independently labelled accepted, rejected and ambiguous cases;
- enough cases for attribution, polarity, timing and source-quality strata;
- no reuse of GM, Honeywell, HP, Boeing or any document already used in 0.3.x inspection as unseen evidence;
- thresholds declared before scoring;
- no outcome access.

## Decision

An Evidence Engine 0.3.5 development phase is warranted, because the failures are frequent, severe enough to block product use, and largely generalisable. It should be narrowly scoped to event factuality, attribution, polarity and evidence-span quality. It should not add predictors, weights, scores or source families.

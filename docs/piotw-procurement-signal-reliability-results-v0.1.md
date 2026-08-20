# PIOTW Procurement Signal Reliability Study v0.1 — Results

Status: **READY_FOR_COMPARE** for the development Detect layer

Method: development source-first reliability study; not independent scientific validation

`scientific_gate_run`: `false`

## Scope

The protocol was committed before additional case retrieval at commit `1e049ee`. The study retained all six fixed exact-identifier entities: Mears Limited (`02519234`), Kier Construction Limited (`02099533`), Balfour Beatty Civil Engineering Limited (`04482405`), Capita Business Services Limited (`02299747`), Mitie Limited (`02938041`) and Serco Limited (`00242246`). No replacement entity was selected after patterns were visible.

The frozen development corpus contains 41 primary Find a Tender award-record references spanning 2021–2025. Underlying-award deduplication retained 39 unique awards and removed two later notice versions/republications. The incomplete 2026 period was not used.

## Coverage diagnostics

| Entity | Unique awards | Versions removed | Publication periods represented | Buyers | Value coverage | Category coverage |
|---|---:|---:|---|---:|---:|---:|
| Balfour Beatty | 4 | 2 | 2022, 2024, 2025 | 4 | 75.0% | 100% |
| Capita | 9 | 0 | 2021–2025 | 8 | 77.8% | 100% |
| Kier | 7 | 0 | 2021, 2023–2025 | 2 | 0% | 100% |
| Mears | 7 | 0 | 2021–2025 | 2 | 0% | 100% |
| Mitie | 7 | 0 | 2022–2025 | 3 | 85.7% | 100% |
| Serco | 5 | 0 | 2022–2025 | 5 | 80.0% | 100% |

These are counts within the retained source evidence, not estimates of total company awards. Exact-identifier resolution was complete for retained records. Missing periods remain unknown coverage rather than zero activity.

## Source-first findings

### Raw award count

**RETIRED.** It must not create or corroborate an operational condition. Kier's apparent rise was reproduced, but the underlying record was concentrated in two buyer labels, had no usable values and included a missing year. Mitie's apparent jump was substantially driven by several lots published by one NHS framework buyer. Balfour Beatty showed how later notices can restate an underlying framework or award. Notice-count acceleration therefore measures publication behaviour at least as much as company activity.

### Buyer breadth

**CORROBORATION ONLY.** Distinct resolved buyers are factual and may strengthen a condition established independently elsewhere. The source does not provide a complete buyer denominator, so breadth cannot independently qualify a condition.

### Award category mix

**CORROBORATION ONLY.** Repeated, deduplicated and source-qualified categories can support an independently established capability or investment theme. Framework categorisation and incomplete coverage prevent a standalone category-shift condition.

### Disclosed contract value

**FACTUAL ONLY.** Value coverage ranged from 0% to 85.7%. Values may be framework ceilings, whole-lot values, multi-supplier totals or estimates rather than attributable supplier revenue. They are preserved with source semantics but cannot drive qualification or corroboration in v0.1.

### Supplier concentration/diversification

**FACTUAL ONLY.** This supplier-side corpus does not expose a denominator-complete company purchasing ledger. The feature cannot currently measure the company's own supplier concentration.

### New strategic relationship

**CORROBORATION ONLY.** A directly named buyer/supplier relationship may support another source-backed condition, but the notice alone does not establish strategic materiality or group-wide significance.

### Persistent procurement theme

**CORROBORATION ONLY.** A repeated theme may support another source-backed condition after deduplication and coverage checks. It cannot independently qualify one.

## Negative controls

The controls behaved as intended:

- Balfour Beatty exposed two later notices tied to already represented underlying awards; deduplication removed them.
- Kier and Mears exposed repeated-buyer concentration and missing-value failure.
- Kier exposed volatile publication counts without sufficiently broad buyer or value evidence.
- Mitie exposed a one-buyer, multi-lot framework effect that could look like acceleration.
- Balfour Beatty, Capita, Mitie and Serco exposed periods dominated by one disclosed headline value.
- Missing years were retained as unavailable, never filled with zero.

No negative control supported a standalone operational conclusion from procurement.

## Versioned policy

The enforceable policy is `config/conditions/procurement_feature_role_policy_v0_1.json`. `ProcurementFamilyAdapter` v0.3 preserves the factual features but emits no standalone procurement condition because no v0.1 feature is independently condition-eligible. Corroboration-only features activate only when another evidence family has already established a candidate; factual-only and retired features cannot create or support one.

## Detect readiness

The three procurement publication-count decisions responsible for ambiguity in the preserved 14-decision review are no longer eligible condition decisions under the retired-feature policy. Estate and leadership policies were not rerun or modified.

The remaining 11 eligible preserved decisions contain nine qualified conditions, all nine source-first judged correct. Qualified precision is 100%; ambiguity is 0%; factual accuracy, entity scope and provenance are 100%; severe false positives and unhandled contradictions are zero.

The final development Detect status is therefore:

`READY_FOR_COMPARE`

This does not change the separate Evidence Engine independent-scientific readiness status, does not validate prediction, and does not claim procurement independently detects conditions.

## Next P0

Build **General Peer / Historical Comparison Engine v0.1**. Begin with company-own-history comparison, comparable condition-level features, explicit peer-cohort definitions and coverage-aware normalisation. Do not create a headline PIOTW score.

## Primary sources

All study rows and URLs are preserved in `data/derived/piotw_procurement_signal_reliability_v0_1_results.json`. Primary records are from [UK Find a Tender](https://www.find-tender.service.gov.uk/).

# PIOTW Real Company Lab v1

## Purpose

Real Company Lab tests whether PIOTW can reconstruct a recognisable operating history from public evidence for a company the founder knows well. It is a product and historical-reconstruction lab, not scientific validation.

The first active entity is Travis Perkins plc. The lab contains seven point-in-time checkpoints from the 2021 full-year results (published in 2022) through the 2026 half-year results.

## Hard evidence boundary

| Class | Permitted use | Storage |
|---|---|---|
| `PUBLIC_EVIDENCE` | Source and atomic factual observation | Travis Perkins lab source/observation store |
| `PIOTW_DERIVATION` | Exploratory observation-to-dimension relationship and product synthesis | Snapshot read model only |
| `FOUNDER_RETROSPECTIVE` | Later comparison with lived experience | Browser-local retrospective record only |

Founder retrospective is never evidence, never a feature and never an input to the illustrative position.

## Entity model

`Travis Perkins plc` is represented as the Group. Travis Perkins Merchanting, Toolstation, BSS, CCF and Keyline are distinct child entities prepared for later work. Every observation has an entity, Group/business-unit scope and source. A business-unit observation is not silently promoted to a Group fact.

## Product routes

- `/lab` — Real Company Lab index and entity scope.
- `/lab/travis-perkins` — latest Travis Perkins reconstruction.
- `/lab/travis-perkins?as_of=YYYY-MM-DD` — a historical point-in-time view.

Every rating, percentile, probability and analytical implication is labelled illustrative and not validated. The facts beneath them are linked to real public company sources.

## Current limitations

- The corpus is deliberately bounded to seven high-quality issuer reporting checkpoints.
- Careers history, Companies House records and broader media evidence are not yet included.
- The illustrative rating and forward-event probability are authored product concepts, not a trained or calibrated model.
- Public evidence is uneven by dimension. Sparse dimensions visibly remain insufficient.
- Historical comparison is not outcome adjudication and makes no claim of prediction accuracy.

`scientific_gate_run = false`.

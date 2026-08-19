# Evidence Engine 0.3.2 table-context rules

Status: development QA only. Formal gold and Model 2 readiness are unaffected.

## Evidence structures

Every candidate is typed as narrative sentence, narrative paragraph, table cell, table row, table heading, table footnote, accounting reconciliation, list/bullet, or malformed/unknown fragment where the source permits. The current HTML/PDF text layer reliably distinguishes only a subset; unresolvable structure is labelled rather than guessed.

Table-derived candidates also retain structure quality, period binding, row label, column heading, cell value, page/section and surrounding context. Missing geometry remains `null`, rather than being fabricated.

## Period binding

Explicit years bind candidates to current period, comparative period, current-and-comparative, future period, multi-year history or unknown. Mixed past/future years without the current period are treated as a broken or joined fragment. Row position alone never establishes the current period.

## Operational promotion

An accounting row containing restructuring, impairment, severance, closure or transformation language remains a financial observation. It becomes an operational event only when direct source wording says the company initiated, announced, commenced or implemented current activity. Historical, comparative, completed, accounting-only and malformed spans are rejected or held ambiguous.

Examples of sufficient support include “During 2024 we initiated…”, “the company is implementing…” and “we commenced…”. A current charge amount by itself is insufficient.

## Malformed fragments

Low-quality flags include mismatched parentheses, dense numeric tokens with little grammar, repeated year/GAAP/adjusted headings, page-header contamination and mixed period order. Low-quality accounting candidates fail closed. Coherent narrative facts are not suppressed solely because a page number or table heading is present.

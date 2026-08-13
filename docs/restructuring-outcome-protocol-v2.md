# Restructuring outcome protocol v2

Status: frozen before v2 outcome adjudication
Target: first public announcement of a previously unannounced qualifying restructuring within 365 calendar days after cutoff

## Qualifying events

At least one of the following must be supported by a dated issuer regulated announcement, company disclosure or filed annual/interim report:

1. A named or explicitly described group, division or material subsidiary restructuring/reorganisation programme.
2. A redundancy or formal consultation programme affecting at least 5% of group employees, at least 100 roles, or explicitly described by the issuer as material/significant.
3. A plant/site closure, consolidation or permanent material capacity reduction.
4. A group/division cost programme with quantified recurring savings of at least 2% of the latest pre-cutoff annual operating-cost base, or described as material/significant and accompanied by restructuring/exceptional charges.
5. A substantive operating-model restructuring that changes reporting lines, divisional structure, delivery footprint or operating responsibility and meets a materiality rule above.
6. A division or subsidiary programme only where that unit is material to the listed parent (at least 10% of group revenue/assets/employees, or explicitly material) or the programme meets a group-level threshold.

Expansion-related reconfiguration qualifies only when it independently includes a permanent closure, qualifying redundancy/capacity reduction or material restructuring programme. Capacity expansion alone does not qualify.

## Exclusions

- A programme publicly announced on or before cutoff; later implementation, charges, savings updates, scope repetitions and completion are the same event.
- Repeated announcements without a distinct newly authorised programme.
- Continuous improvement, ordinary productivity work or unquantified local adjustments.
- Transformation programmes limited to technology, culture, strategy or process unless they also meet a qualifying restructuring/materiality rule.
- Management appointments, departures or reporting-line changes without a qualifying programme.
- Ordinary acquisitions, integrations already inherent in an announced acquisition, disposals, demergers and portfolio management.
- A divestment qualifies only if explicitly part of a qualifying operational restructuring rather than ordinary portfolio strategy.
- Profit warnings, impairments, refinancing and capex cuts without a qualifying programme.
- Temporary shutdowns, strike responses or reversible production changes.

## New versus continuing programmes

The unit is the underlying authorised intervention, not each disclosure or accounting charge. A post-cutoff expansion of an existing programme is new only if the issuer clearly identifies a distinct authorisation and it independently meets materiality. Otherwise it remains excluded. Implementation date and accounting-recognition date never replace the first public announcement date.

## Dates and windows

- The window is `(cutoff, cutoff + 365 days]`.
- `outcome_date` is the earliest evidenced public availability date of the qualifying announcement.
- When only a month is evidenced, use the month's final calendar day and set `date_precision=month`.
- When only a year is evidenced, the case is `uncertain`; do not invent a day.
- Announcements exactly on cutoff are pre-existing and excluded. Announcements exactly 365 days after cutoff are inside the window.

## Parent and subsidiary treatment

Map an event to the listed parent controlling the affected entity on the announcement date. Do not double-count the same event for parent and subsidiary. If ownership changes during the horizon, use the parent at announcement and record the corporate transition. A subsidiary event below the materiality rule is adjacent-outcome evidence, not a positive.

## Adjudication

Allowed labels are `positive`, `negative`, and `uncertain`. A negative requires review of the full issuer announcement/results archive across the window and the first results document after the window. An uncertain label is excluded from primary scoring and must identify the unresolved criterion.

Adjudicators see company, cutoff, window, candidate evidence, source/date and event description only. They must not see PIOTW probability, rank, feature contributions or comparator output. Each decision records adjudicator identity, UTC timestamp, source, note, exclusion rule and event date. Disagreements remain unresolved until a predesignated reconciliation decision; raw adjudications are never overwritten.

This document clarifies v1 but does not broaden its substantive target.

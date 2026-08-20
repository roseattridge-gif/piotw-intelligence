# PIOTW Multi-Family Condition Policy Review Extension v0.2 — Protocol

Status: frozen before new evidence selection and evaluation

Methodological status: development methodology review; not independent scientific validation

Cutoff: 19 August 2026 23:59:59 UTC

## Purpose

Resolve the single scope failure in the frozen v0.1 review without redesigning qualification, changing thresholds or starting Compare. The original 11 decisions remain immutable. This extension must contribute at least one new reviewed decision and bring the combined review to at least 12.

## Selection

### Leadership / organisation

Search development-safe UK-listed issuers alphabetically, excluding the original seven-company sample and every frozen restructuring-cohort company. Select the first issuer for which a primary issuer source explicitly describes an operating-model, accountability, reporting-line, role-creation/removal or business-unit leadership redesign. Routine appointments and vague change language are ineligible.

### Procurement

Deepen only Mears Limited and Kier Construction Limited. Include UK Find a Tender contract-award notices only when the legal supplier name and company number match exactly. Use calendar publication year as the comparison period. Exclude pipeline, planning, tender, prior-information and modification-only notices and deduplicate republications or amendments of one underlying award.

The comparable denominator is the count of deduplicated, resolved contract-award notices from this one regime. Absence is missing publication coverage, not zero company activity.

### Careers

Collect only if normally due. Careers cannot substitute for the required leadership case.

## Frozen policy and gate

The unchanged qualification policy is `piotw-condition-qualification-policy-v0.1-development`, SHA-256 `b5af92d2c913a39e0bd756c0a5e17549fc5f02ec3eaa0c5af871b7f8fa26e97d`.

The v0.1 readiness thresholds are reused exactly: factual accuracy 95%; entity scope 100%; qualified precision 90%; false-negative rate no more than 10%; ambiguity no more than 20%; provenance 100%; no severe false positives; no unhandled contradictions; at least two stable family policies; no retired policy.

Possible final statuses are exactly:

- `READY_FOR_COMPARE`
- `NOT_READY_FALSE_POSITIVE_RISK`
- `NOT_READY_FALSE_NEGATIVE_RISK`
- `NOT_READY_ENTITY_RESOLUTION`
- `NOT_READY_POLICY_INSTABILITY`
- `NOT_READY_INSUFFICIENT_REVIEW_SCOPE`

Risk failures take precedence over scope and readiness.

## Source-first review

The new decision is classified as correct qualification, correct withhold, false positive, false negative, ambiguous/needs more evidence, entity-resolution error or feature/policy error. Review checks factual accuracy, scope, candidate validity, history, materiality, persistence, corroboration, contradiction, result and whether the condition is worth operational investigation.

## Stop rule

After freezing this protocol, select exactly the first eligible leadership case and all qualifying same-regime notices for the two named procurement entities through the cutoff. Run once. Do not add replacement cases, modify labels or thresholds, or rerun after aggregate results are visible. A procurement policy revision may be proposed after the run but cannot be treated as stable in this sprint.

`scientific_gate_run` remains `false`.

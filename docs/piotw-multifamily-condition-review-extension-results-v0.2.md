# PIOTW Multi-Family Condition Policy Review Extension v0.2 — Results

Final status: **`NOT_READY_POLICY_INSTABILITY`**

Method: development methodology review; not independent scientific validation

Cutoff: 19 August 2026 23:59:59 UTC

Frozen qualification policy: `piotw-condition-qualification-policy-v0.1-development`

Policy SHA-256: `b5af92d2c913a39e0bd756c0a5e17549fc5f02ec3eaa0c5af871b7f8fa26e97d`

`scientific_gate_run`: `false`

## Extension evidence

The preregistered alphabetical search selected abrdn as the first eligible new leadership/organisation case outside the original sample and frozen restructuring cohort. Its 2024 annual report directly described:

- a new, smaller Group Operating Committee;
- a broadened Executive Leadership Team with greater client expertise;
- scorecards cascaded through each business with ultimate accountability at executive level.

This is an operating-model and accountability redesign, not a routine appointment.

Procurement was rebuilt within one source boundary: UK Find a Tender contract-award notices, calendar publication years, exact legal name plus Companies House identifier, contract-award notices only, and underlying-award deduplication. Mears Limited (`02519234`) had five comparison periods from 2021–2025. Kier Construction Limited (`02099533`) had four observed comparison periods from 2021–2025, with no retained 2022 notice.

## New decisions

| Company | Candidate | Engine | Source-first review | Reason |
|---|---|---|---|---|
| abrdn | Organisational restructuring | QUALIFIED | CORRECT QUALIFICATION | Direct primary evidence established committee, leadership and accountability redesign. |
| Mears Group | Procurement activity acceleration | INSUFFICIENT_EVIDENCE | CORRECT WITHHOLD | Annual notice counts reversed direction; persistence failed. |
| Kier Group | Procurement activity acceleration | QUALIFIED | AMBIGUOUS / NEEDS MORE EVIDENCE | Counts rose from one to three retained notices, but buyer-driven publication coverage is sparse and incomplete. |

No severe false positive, false negative, entity-resolution error, provenance failure or unhandled contradiction was identified. Kier was not labelled a confirmed false positive because the movement is factually real and worth investigating, but the evidence cannot establish a company operational condition confidently.

## Combined gate

The original 11 decisions plus three extension decisions produce 14 reviewed decisions.

| Gate measure | Result | Threshold | Outcome |
|---|---:|---:|---|
| Factual observation accuracy | 14/14 (100%) | ≥95% | Pass |
| Entity scope accuracy | 14/14 (100%) | 100% | Pass |
| Qualified-condition precision | 9/10 (90%) | ≥90% | Pass |
| False-negative rate | 0/9 (0%) | ≤10% | Pass |
| Ambiguous cases | 3/14 (21.43%) | ≤20% | **Fail** |
| Provenance completeness | 14/14 (100%) | 100% | Pass |
| Severe false positives | 0 | 0 | Pass |
| Unhandled contradictions | 0 | 0 | Pass |
| Stable family policies | 2 | ≥2 | Pass |

The initial reporting code incorrectly emitted `READY_FOR_COMPARE` because it omitted the frozen ambiguity-rate check. The condition engine was not rerun. A gate-only correction applied the missing preregistered check to the preserved results and recorded the audit trail in the machine-readable output.

Final status: **`NOT_READY_POLICY_INSTABILITY`**.

## Family conclusions

### Leadership / organisation

The policy now has three substantive operating-structure cases across Kingfisher, Kier and abrdn, plus a routine Howdens appointment that remained factual-only. The new abrdn result was a correct qualification. The leadership policy is development-usable and remains conservative, although it is not independently validated.

### Procurement

The source-specific boundary is now explicit and reproducible, but the qualification policy is not usable as a stable condition policy. It can mistake an increase in a small, buyer-driven set of published notices for a company-level operational acceleration. The factual history is useful; the condition inference is not yet stable.

Proposed future rule, not implemented or rerun here: require explicit source-coverage diagnostics and distinguish buyer/notice-regime coverage from company activity before a procurement-count candidate can qualify. This is source-specific. Testing it would require a newly preregistered procurement review, and fitting it to Kier alone would create severe overfitting risk.

## Readiness and next P0

Compare must not start. The single remaining Detect blocker is procurement policy stability: the source boundary is sound, but notice-count completeness is not. The next P0 is a small preregistered procurement-policy study across several exact-identifier suppliers within the same Find a Tender award regime, including explicit coverage denominators and negative controls. Estate and leadership can be carried forward unchanged while procurement remains factual-only.

# PIOTW Unknown-Company Orchestrator v0.1

## Purpose and boundary

This is the first reusable path from an approved company identity to the canonical `piotw-company-intelligence-v0.1` read model. It deliberately produces a sparse object when PIOTW lacks evidence or analytical capability. It does not access frozen experiments, outcomes, Model 2, or introduce a company score.

## Implemented runtime

```mermaid
flowchart LR
    A["Company name or approved ID + cutoff"] --> B["Resolve identity in approved source registry"]
    B --> C["Inspect collector availability and stored health"]
    C --> D["Build evidence manifest"]
    D --> E["Exclude records unavailable by cutoff"]
    E --> F["Create deterministic factual observations only"]
    F --> G["Assess coverage and capability status"]
    G --> H["Assemble canonical intelligence object"]
    H --> I["Validate contract and evidence references"]
    I --> J["Persist run artefacts and generic frontend JSON"]
    J --> K["Render /intelligence/[companyId]/value"]
```

The implementation reuses the approved careers registry, careers longitudinal evidence store, stored health and hashes, canonical Pydantic contract assembler, and existing generic frontend loader. No parallel contract or company page was introduced.

## Identity, source state and cutoff discipline

The command accepts a company name or approved company ID, an ISO-8601 cutoff, and an optional explicit approved entity ID. Matching is exact by ID or normalized exact company name; unresolved or ambiguous identities fail.

Each source family is marked separately as `AVAILABLE`, `UNAVAILABLE`, `FAILED`, or `NO_HISTORY`. Procurement, issuer disclosures and regulatory notices remain unavailable because no approved reusable company attachment is wired into this path. Absence never becomes zero or neutral.

Every collection attempt is represented in `piotw-evidence-manifest-v0.1`, including excluded future or failed records. Records retain source IDs, timestamps, collector version, URL, hash, entity scope, health, cutoff eligibility, inclusion decision and reason. The manifest hash and run ID derive from the normalized inputs. Identical stored inputs and cutoff reproduce the same object.

## Detect and downstream stages

The orchestrator now passes factual careers observations into Operational Condition Qualification Engine v0.1. Candidate assessments are carried separately from `conditions[]`. Direction and materiality remain `UNKNOWN` unless every required development-policy test passes; the object does not interpret a one-period movement as growth, contraction, pressure or health.

| Stage | Status | Reason |
|---|---|---|
| Detect | `INSUFFICIENT_EVIDENCE` | A factual change exists, but no validated condition engine establishes meaning or materiality. |
| Compare | `INSUFFICIENT_EVIDENCE` | No approved coverage-normalized historical or peer benchmark. |
| Predict | `NOT_BUILT` | No validated operational predictive-pattern engine. |
| Prescribe | `WITHHELD` | No driver-specific evidence supports an intervention. |
| Quantify | `WITHHELD` | No supported intervention or financial mechanism exists. |

## Unknown-company development run

Cloudflare was selected because it was already in the approved careers registry, had real stored collector history, and had no bespoke canonical intelligence object. It was not selected for a desired conclusion.

- Input: `cloudflare`
- Cutoff: `2026-08-19T00:00:00Z`
- Run ID: `uc-cloudflare-20260819T000000Z-a38699359d13`
- Sources: careers/ATS available; procurement, issuer disclosures and regulatory notices unavailable
- Evidence: 2 cutoff-safe healthy careers snapshots with hashes
- Observation: 305 then 297 open postings; deterministic change -8
- Candidate: hiring contraction, `INSUFFICIENT_EVIDENCE` because history, magnitude and persistence tests failed
- Qualified conditions: 0
- Manual intervention: none
- Downstream output: no benchmark, probability, recommendation or financial value
- Generic route: `/intelligence/cloudflare/value`

## Actual next bottleneck

The qualification architecture now exists, but the first bottleneck remains **Detect evidence depth and policy validation**. The run knows a count changed and can show exactly why the candidate failed. It cannot establish whether the movement is persistent or operationally material. With one source family and two snapshots, Compare and every later stage lack supported input.

The smallest next P0 is deeper real longitudinal history plus source-first review of the development qualification decisions. Preserve per-snapshot lifecycle and mix aggregates, exercise persistence on multiple real companies, and attach one approved procurement history before changing thresholds or building Compare.

## Commands

```bash
make unknown-company-demo
.venv/bin/python scripts/run_unknown_company_v01.py --company cloudflare --as-of 2026-08-19T00:00:00Z
```

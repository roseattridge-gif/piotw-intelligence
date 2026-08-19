# Evidence Engine 0.3 - frozen Model 2 readiness gate

Gate version: **0.3.0**. This gate is fixed before any independent benchmark scoring. It must not be changed in response to aggregate results.

## Mandatory validity conditions

Independent human-first observation and event annotations must be completed without PIOTW output, frozen by SHA-256, and pass integrity verification. Review timings and at least 100 independently labelled jobs must exist. Any missing condition makes the decision **NOT READY**.

## Thresholds

| Measure | Ready with human review | Ready for Model 2 development |
|---|---:|---:|
| Overall numerical accuracy | >=80% | >=90% |
| Each strategic metric, minimum 10 labels | >=70% | >=80% |
| Severe-error rate | <=5% | <=2% |
| Period and accounting-basis accuracy | >=90% | >=95% |
| Event precision / recall | >=80% / >=65% | >=90% / >=80% |
| Provenance completeness | >=95% | >=98% |
| Longitudinal feature accuracy | >=80% | >=90% |
| Manual correction rate | <=50% | <=30% |
| Assisted review time reduction | >=15% | >=35% |
| Jobs classification accuracy | >=75% | >=85% |
| False closure rate on resolved cases | <=5% | <=2% |

Strategic metrics are EBITDA, adjusted EBITDA, operating margin, adjusted operating margin, free cash flow, cash conversion, and net debt/net cash. A result cannot pass the higher gate if any strategic metric lacks ten independent labels. Human review remains permitted; complete provenance and auditable corrections are mandatory.

## Decision rule

- **NOT READY**: any validity condition is missing, any severe-error limit fails, or the lower thresholds are not all met.
- **READY WITH HUMAN REVIEW**: all validity conditions and all lower thresholds are met, but one or more higher thresholds fail.
- **READY FOR MODEL 2 DEVELOPMENT**: all validity conditions and all higher thresholds are met.

This gate authorises no model training. It only informs a later, separately approved phase.

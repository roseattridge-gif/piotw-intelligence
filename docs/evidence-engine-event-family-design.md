# Evidence Engine event-family design

## Shared pipeline

```text
immutable source evidence
  -> deterministic candidate + exact pointer
  -> shared actuality, attribution and provenance checks
  -> event-family router
  -> family identity/polarity/scope contract
  -> accepted | rejected | ambiguous
  -> one canonical event linked to one or more ontology dimensions
```

The shared layer owns evidence transport, source hashes, exact spans, time, target company resolution, provider/schema validation, deduplication and fail-closed behaviour. Family logic owns semantic identity.

## Candidate families

| Family | Representative events | Required distinction |
|---|---|---|
| Restructuring and cost action | restructuring, cost reduction, efficiency, simplification | Named programme versus action; provision versus operational intervention; issuer versus customer/supplier |
| Workforce | hiring, redundancy, workforce reduction, labour constraint | Hiring versus contraction; issuer workforce versus industry labour market |
| Delivery, capacity and sites | site closure/opening, capacity reduction/expansion, disruption | Open versus close; temporary disruption versus structural capacity change |
| Demand and growth | revenue, orders, demand, volume, backlog | Increase versus decline; revenue growth versus cost growth; realised change versus aspiration |
| Supply chain and resilience | shortages, constraints, supplier disruption | Actual target-company effect versus generic risk or supplier-only event |
| Quality and regulatory | recalls, quality failures, operating restrictions | Actual notice/event versus compliance boilerplate |
| Leadership and change execution | transformation, leadership change | Current issuer action versus biographies, prior employers or historical programmes |

## Implemented proof contracts

`DemandGrowthFamilyVerifier` requires a demand-side object such as revenue, sales, orders, backlog, demand or volume and an observed direction. It explicitly rejects expense growth as demand growth and aspirations without observed change.

`RestructuringCostActionFamilyVerifier` requires an issuer action such as announcement, implementation, initiation, pursuit or recognised/incurred intervention. It rejects product/programme names without action, explicit customer/supplier actions, and generic hypothetical language.

Both are intentionally narrow. Unsupported families return `ambiguous/family_not_implemented`; they do not fall back to an apparently authoritative generic decision.

## Testing rule

Every family must have:

- positive and negative identity cases;
- polarity pairs;
- target, subsidiary and third-party attribution cases;
- current, planned, historical and hypothetical cases;
- exact-provenance assertions;
- contaminated regression cases labelled as development only;
- a frozen fresh-validation protocol before any new scientific evaluation.


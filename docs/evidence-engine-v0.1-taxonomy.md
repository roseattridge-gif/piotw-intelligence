# Evidence Engine 0.1 — event taxonomy

The machine-readable authority is `config/evidence/event_taxonomy_v0_1.yaml`.

## Groups and atomic events

| Group | Implemented event types |
|---|---|
| Financial pressure | margin deterioration, cash deterioration, leverage increase, working-capital pressure, liquidity concern, refinancing, covenant concern |
| Operational pressure | demand weakness, supply-chain constraint, labour constraint, inflation pressure, destocking, customer weakness, operational disruption, capacity mismatch |
| Intervention | cost reduction, restructuring, efficiency programme, simplification, transformation, footprint reduction, site closure, capacity reduction, redundancy, workforce reduction |
| Expansion | hiring, capex growth, new facility, capacity expansion, geographic expansion, major investment, skills investment |
| Contrary/strength | margin improvement, cash improvement, deleveraging, order-book strength, demand growth, liquidity strength, recovery language, growth language |

## Extraction behaviour

The 0.1 extractor splits source text into retained sentences and applies versioned regular-expression patterns. Each match records the exact sentence, location, source evidence ID, period/date, confidence, quantified flag, taxonomy group, and parser/taxonomy version.

It deliberately does not calculate Pressure or Expansion. These are taxonomy folders, not scores.

`severity` remains null unless severity is objectively extractable. “New” means no earlier accepted event of that type exists in the available periods; “persistent” means it appeared previously. Neither is an outcome judgment.

## Known taxonomy limitations

- Negation and subtle context are not yet fully handled.
- Boilerplate and repeated references may create separate events unless their normalized spans match exactly.
- “Transformation” can describe growth investment or defensive intervention; deterministic matching cannot always distinguish intent.
- Synonyms not represented in the YAML are missed.
- Quantification detection identifies explicit numbers but does not determine economic materiality.
- Segment-level and group-level statements are not yet separately typed.

These are reviewable candidate classifications. The original evidence sentence remains authoritative.


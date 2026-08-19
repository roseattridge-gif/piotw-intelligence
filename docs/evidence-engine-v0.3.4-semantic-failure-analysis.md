# Evidence Engine 0.3.4 semantic failure analysis

Status: development analysis of a preserved failed scientific version. Evidence Engine 0.3.4 remains unchanged and unfrozen. No outcomes were accessed.

## Scope and methodological boundary

This analysis covers the nine inspected false positives accepted in the GM/Honeywell/HP subset and the two retained missed events in the six-document diagnostic. The severe false positive and attribution error are subsets of the nine, not additional cases. These cases are now contaminated for future validation: they may inform 0.3.5 development, but must never again be described as unseen evidence.

## Failure table

| # | Company / document | Candidate and evidence | Surrounding context | Model → expected | Failure class and diagnosis | Rule vs semantic / design / source | Generalisable? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | General Motors / `ee02-gm-0001467858-23-000029` | `labour_constraint`: “As a result, we may be subject to an increased risk of strikes, work stoppages or other types of conflicts with labor unions and employees.” | Collective-bargaining agreements were due for negotiation; the text describes increased risk, not an occurring strike. | ACCEPT `DIRECT_CURRENT_EVENT` → REJECT hypothetical risk | Hypothetical/conditional language; the model treated exposure to risk as an actual current constraint. | Deterministically preventable when “may be subject to … risk” lacks an occurrence verb; semantic review still needed when a sentence combines realised and future effects. | Yes—common risk-factor construction. |
| 2 | General Motors / `ee02-gm-0001467858-23-000029` | `restructuring`: “and elsewhere involving various issues, including … claims and actions arising from restructurings and divestitures of operations and assets.” | A list of legal proceedings and claims. No current operational programme, scope or date is asserted. | ACCEPT `DIRECT_CURRENT_EVENT` → REJECT | Legal reference / programme discussion; severe because it invents a current restructuring. | Deterministically preventable in litigation-list context unless an adjacent factual statement establishes the company programme. | Yes—legal contingencies regularly enumerate event words. |
| 3 | General Motors / `ee02-gm-0001467858-24-000031` | Same labour-risk wording as case 1. | Later report repeats the collective-bargaining risk disclosure. | ACCEPT → REJECT | Repeated hypothetical-risk failure. | Same general rule as case 1; deduplicate the regression concept across periods while retaining both document cases. | Yes. |
| 4 | Honeywell / `ee02-hon-0000773840-23-000013` | `supply_chain_constraint`: “manufactured products/services 19 % 62 % 53 % 37 % … RAW MATERIALS … during 2022, we experienced supply chain constraints for certain raw materials.” | PDF extraction joined table debris, a risk cross-reference and a raw-material statement. | ACCEPT `DIRECT_CURRENT_EVENT` → REJECT under the frozen inspection label | Malformed PDF/layout context; the factual clause is plausible, but the supplied inspection label treats the joined span as unreliable evidence. | Source-quality problem first. Segment the page and re-extract a clean sentence before semantic adjudication; do not create a rule saying this issuer’s wording is false. | Yes—multi-column/table joins are common. |
| 5 | Honeywell / `ee02-hon-0000773840-23-000013` | `supply_chain_constraint`: “Throughout 2022 and continuing into 2023, the global economy experienced and continues to experience significant supply chain disruptions…” | Heading is “MACROECONOMIC CONDITIONS”; subject is the global economy. | ACCEPT `DIRECT_ONGOING_CONDITION`, target company → REJECT | Third-party/industry attribution; this is the single attribution error. | Deterministically preventable when the grammatical subject is explicitly global economy/industry and no target-company effect is asserted. | Yes. |
| 6 | HP / `ee02-hpq-0000047217-23-000100` | `cost_reduction`: “Structural cost savings represent gross reductions in costs driven by operational efficiency, digital transformation, and portfolio optimization.” | Definition of a non-GAAP/management measure. | ACCEPT `DIRECT_CURRENT_EVENT` → REJECT | Accounting definition/reference, not an implemented intervention. | Deterministically preventable using definitional constructions (“X represents/means/is defined as”) and accounting-policy/note context. | Yes. |
| 7 | HP / `ee02-hpq-0000047217-23-000100` | `growth_language`: “our net revenue growth has been impacted … by fluctuations in foreign currency exchange rates.” | Constant-currency methodology explains an adverse/neutral translation effect. | ACCEPT `DIRECT_ONGOING_CONDITION` → REJECT as positive growth | Taxonomy polarity/definition ambiguity: containing “growth” does not establish growth. | Taxonomy/design clarification plus semantic polarity. “Growth language” is too lexical; replace with factual demand/revenue direction where supported. | Yes. |
| 8 | HP / `ee02-hpq-0000047217-23-000100` | `growth_language`: “Operating expenses as a percentage of revenue increased primarily driven by variable compensation and the acquisition of Poly…” | The increased item is expense ratio, not revenue or demand. | ACCEPT `DIRECT_CURRENT_EVENT` → REJECT | Taxonomy overlap / semantic reasoning failure caused by the token “increased”. | Deterministic candidate generation should require the growth term’s grammatical object to be demand, orders, volume or revenue—not expense. | Yes. |
| 9 | HP / `ee02-hpq-0000047217-23-000100` | `cost_reduction`: “(5) Cost Savings Plans.” | Heading is adjacent to a real approved restructuring-plan paragraph, but the accepted evidence pointer resolves only to the heading. | ACCEPT `DIRECT_PLANNED_EVENT` → REJECT for insufficient direct evidence | Heading/cross-reference and evidence-window mismatch. | Deterministically reject heading-only evidence; candidate construction may separately emit the adjacent factual sentence with its own exact span. | Yes. |
| 10 | Boeing / `ee03-ba-0000012927-23-000007` | Missed `margin_deterioration`: “This market environment has resulted in intense pressures on pricing, and we expect these pressures to continue or intensify.” | Industry Competitiveness section, PDF p50. | No candidate → expected positive condition | Taxonomy coverage gap: pricing pressure is not captured by the narrow margin-decline pattern. | Semantically adjudicable after a general candidate pattern for realised pricing pressure; taxonomy must distinguish pricing pressure from observed margin deterioration. | Yes. |
| 11 | Boeing / `ee03-ba-0000012927-23-000007` | Missed `demand_weakness`: “BGS total backlog … decreased by 6% from $20,496 million at December 31, 2021.” | Backlog table/narrative, PDF p52; independent annotation marked ambiguity. | No candidate → expected positive/ambiguous demand condition | Numerically expressed event and table extraction gap. | Source extraction plus taxonomy design: backlog decline is an objective observation; whether it means demand weakness requires context and should not be forced. | Yes, especially order-driven sectors. |

## Root-cause taxonomy and frequency

Counts are over 11 unique cases. Categories can overlap where one failure has more than one cause.

| Root cause | Cases | Count | Primary handling |
| --- | --- | ---: | --- |
| Hypothetical/conditional language | 1, 3 | 2 | Deterministic cue plus semantic fallback |
| Legal/accounting/heading reference rather than event | 2, 6, 9 | 3 | Deterministic structural/context exclusion |
| Third-party or industry attribution | 5 | 1 | Deterministic entity anchoring plus semantic fallback |
| Malformed PDF/layout context | 4 | 1 | Source segmentation and provenance repair |
| Taxonomy polarity/overlap | 7, 8, 10, 11 | 4 | Clarify observation and event definitions before extraction |
| Evidence-window insufficiency | 9 | 1 | Candidate/span construction repair |
| Numerically expressed condition not lexically captured | 11 | 1 | Objective observation extraction first |
| Semantic reasoning failure | 1, 2, 3, 5, 6, 7, 8, 9 | 8 | Stronger constrained adjudication after deterministic fixes |

No inspected failure was primarily a biography, quoted external material, completed historical event or multi-event ambiguity in this subset. Those remain known regression classes from earlier development and should stay covered.

## Rules versus semantic verification

### Deterministically preventable

- explicit “risk of / may be subject to” statements with no realised occurrence;
- litigation-list, accounting-definition and heading-only candidate spans;
- explicit global economy/industry subjects without a target-company effect;
- growth candidates whose grammatical object is cost or expense rather than demand/revenue/orders/volume;
- malformed spans that fail structural-quality checks.

These are proposed as general classes, not issuer exceptions. Each rule must be tested against supported counterexamples before adoption.

### Semantically adjudicable

- mixed realised-and-forward-looking sentences;
- company exposure embedded in broader industry discussion;
- planned versus implemented interventions;
- whether pricing pressure directly describes the target company;
- segment versus group scope.

### Taxonomy/design ambiguity

- `growth_language` is a lexical category, not a clean factual event;
- pricing pressure is not identical to margin deterioration;
- backlog decline is an objective observation whose demand interpretation is sector/context dependent;
- dealer restructuring demonstrates that payer, beneficiary and operational subject can differ.

### Source-quality problems

- multi-column/table debris joined to narrative;
- headings returned as the exact evidence instead of the supporting sentence;
- numeric tables without reliable header/period association.

## Contamination register

The following are development-contaminated from this point forward:

- all 30 inspected GM/Honeywell/HP rows in `data/evidence_engine_v0_3_3/new_unseen_inspected_events.csv`;
- the scientific decisions for those documents in Batch `batch_6a832dbf3d2c81909c2ff50f828be0da`;
- the six-document AI-assisted diagnostic, including Boeing events `event-009` and `event-010`;
- the 230-case semantic benchmark and all prior/unseen inspection sets used by the 0.3.4 gate.

They may be regression/development material for 0.3.5. A future quality claim requires genuinely fresh companies, documents and annotations selected before running the changed extractor.

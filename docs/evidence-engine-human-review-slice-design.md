# Evidence Engine human-review slice design

## Purpose

Before 0.3.7 implementation, a qualified human should distinguish extractor failure from label-definition ambiguity on 36 high-value rows. The frozen design is in `data/derived/evidence_engine_v0_3_6_human_review_slice.csv`.

The slice contains:

- Demand/Growth: 6;
- Leadership/Change: 6;
- Quality/Regulatory: 6;
- Restructuring/Cost Action: 5;
- Workforce: 5;
- Delivery/Capacity/Sites: 4;
- Supply Chain/Resilience: 4.

It prioritises all nine false positives, supported labels that conflict with temporal rules, local-versus-semantic disagreements and ambiguous spans.

## Reviewer task

The reviewer should see only the source document, bounded source context, publication date and written observation/event contract—not PIOTW or AI answers. For each row they should record:

1. Does the exact context establish a factual target-company observation?
2. What are subject, action/state and object?
3. Is it actual, ongoing, planned, completed, historical, hypothetical, negated or ambiguous?
4. What reporting/event period applies relative to publication date?
5. What direction/polarity is supported?
6. Is the proposed event identity correct, incorrect or premature?
7. What exact evidence span supports the answer?

Demand rows receive an additional question: does the change evidence demand, or merely price, production, valuation assumptions or an accounting movement?

## Expertise and adjudication

Use two blinded reviewers with financial-reporting literacy and experience interpreting operational company disclosures. A third reviewer adjudicates disagreements against the frozen written contract. Reviewer answers must be frozen before comparison with PIOTW or existing AI-assisted labels.

Do not ask reviewers to assign Pressure, Expansion, risk or prediction scores.

## Why review is required

Forty-five supported labels are marked historical and four hypothetical, despite family contracts that generally exclude those states. That conflict materially affects stage attribution and the meaning of retention. Human review is recommended before 0.3.7 is implemented, not merely before its next gate.

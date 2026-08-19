# Evidence Engine observation-first assessment

## Decision

PIOTW should move to observation-first extraction before another fresh validation gate.

## Why

The 0.3.6 candidate object combines several separate questions:

- did a factual statement occur;
- what entity did it concern;
- what changed;
- when and with what status;
- what direction/polarity applied;
- which event type/family represented it.

That premature bundling caused brittle regex requirements, polarity errors and circular family evaluation. Atomic observations let each question be represented explicitly and tested independently.

## Proposed atomic observation

An accepted observation should contain at least:

- target entity and entity type;
- factual predicate/action;
- object or metric;
- prior and current state/value when available;
- direction/polarity;
- event date/period and status;
- actual, planned, hypothetical, negated or ambiguous actuality;
- group/segment/facility/geography scope;
- exact immutable evidence pointer and bounded context;
- extractor/model/prompt version;
- validation status and review history.

Examples include `site closed`, `headcount reduced`, `capacity increased`, `supplier disrupted`, `executive appointed`, `recall announced` and `backlog declined`. These are factual objects. `Delivery & Capacity` or `Change & Execution` are downstream relationships.

## Expected benefits

- avoids forcing a sentence into a single family before its facts are understood;
- makes positive/negative polarity explicit instead of encoding it in names like `growth_language`;
- normalises timing once against publication date;
- permits multi-dimensional links without duplicating facts;
- gives human reviewers factual questions rather than taxonomy arguments;
- makes evaluation decomposable into extraction, actuality, attribution, timing and mapping accuracy.

## Remaining risks

Observation-first extraction does not remove semantic difficulty. It can still miss implicit facts, conflate historical and current statements, or infer unsupported subjects. Those risks should be controlled with immutable evidence pointers, a bounded context contract, deterministic schema validation, explicit ambiguity and targeted human review—not another family-specific keyword layer.

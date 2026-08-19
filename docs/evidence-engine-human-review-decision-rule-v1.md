# Evidence Engine human-review decision rule v1

## Status

`PREREGISTERED_BEFORE_HUMAN_ANSWERS`

These rules determine what happens before Evidence Engine 0.3.7 implementation. They must not be changed after reviewer answers are inspected.

## Human-human agreement

Calculate exact factual-observation agreement, material overall agreement, timing agreement among joint-YES cases and entity agreement among joint-YES cases.

- **Substantial human agreement:** factual-observation agreement at least 80%, material overall agreement at least 75%, timing agreement at least 75%, and entity agreement at least 90%.
- **High intrinsic ambiguity:** material disagreement exceeds 25% overall, or exceeds 40% within an ambiguity category containing at least five cases.
- Results between these conditions are `MIXED` and require qualitative review of category-level disagreements before implementation.

## Human versus AI-assisted labels

Map adjudicated human `YES/NO/AMBIGUOUS` to AI-assisted `supported/unsupported/ambiguous` only for diagnostic agreement.

- **Substantial AI-label agreement:** at least 75% overall factual-label agreement and no ambiguity category with at least five cases below 60%.
- **Substantial AI-label disagreement:** below 60% overall agreement, or two or more ambiguity categories with at least five cases below 50%.
- Otherwise classify the result as `MIXED`.

## Architecture consequence

1. If humans substantially agree with one another and with AI labels, treat 0.3.6 primarily as extractor-architecture failure and implement the preregistered observation-first substrate.
2. If humans substantially agree with one another but substantially disagree with AI labels, revise and freeze the atomic-observation definitions/schema using the human evidence before implementing 0.3.7.
3. If human-human disagreement is high, preserve `AMBIGUOUS` for the affected concepts, narrow or defer their mapping rules, and do not force binary classification.
4. If results are mixed, resolve the named categories in a versioned methodology decision before implementation; do not average disagreement away.

Human versus 0.3.6 agreement is reported diagnostically but cannot reverse the failed scientific gate or create a readiness claim.

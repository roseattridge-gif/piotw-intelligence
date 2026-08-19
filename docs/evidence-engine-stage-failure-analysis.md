# Evidence Engine stage failure analysis

## Actual 0.3.6 decision path

The implemented path was:

`broad keyword locator → candidate event type/family → local family contract → semantic event decision → accept only when both accept`

The local and semantic decisions were computed independently, but the final AND-gate meant either could veto acceptance.

## Stage findings

### Candidate generation

Candidate-generation recall is **not measurable from this corpus**. All 210 frozen labels were sampled from already surfaced candidates. The data can assess candidate quality, not whether the locator missed unsurfaced facts elsewhere in the documents.

The locator did surface many deliberately unsupported and ambiguous spans, which is compatible with a high-recall candidate stage. It also attached premature event identities such as `growth_language` to negative revenue movement. That early semantic commitment contaminated later routing and polarity decisions.

### Family routing

There were zero recorded label-versus-router mismatches, but labels were created against the candidate's proposed family. This is not an independent routing test.

### Family contracts

Family contracts caused 57/77 misses (74.03%). They were especially brittle for quality, workforce, delivery/capacity and change/execution. The regexes required narrow wording and word order even when the source-first reviewer considered the factual condition supported.

### Shared safety rules

Shared exclusions caused 10/77 misses (12.99%): four hypothetical, four negation and two historical exclusions. Some may be correct contract enforcement rather than extractor failures because supported labels often conflict with the written timing/hypothetical boundary.

### Semantic adjudication

The semantic verifier was the unique blocker for 8/77 misses (10.39%) where the local family contract accepted. Its main reasons were insufficient support, subject ambiguity and generic risk.

It was not a sufficient precision guard: all nine false positives were accepted by both layers. Eight were labelled historical, showing the prompt and deterministic layer did not share a reliable time-normalised representation.

### Provider execution

Two supported candidates had incomplete provider outputs (2.60% of misses). Provider/schema/contract completeness still passed the preregistered threshold and was not the architectural cause.

## Responsibility split diagnosis

The responsibilities are divided incorrectly:

1. The locator assigns an event identity too early.
2. The family regex layer tries to infer factual meaning using fragile lexical patterns.
3. The semantic model repeats factuality, timing, attribution and event classification.
4. The final AND-gate compounds false negatives.
5. Timing and polarity are not normalised once and reused by both layers.
6. Family labels and ontology dimensions are being treated like facts rather than downstream classifications.

The safest parts—immutable evidence pointers, source hashes, exact spans and fail-closed handling—should remain. Event-family meaning should move downstream of atomic factual extraction.

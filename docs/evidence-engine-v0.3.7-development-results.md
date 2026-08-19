# Evidence Engine 0.3.7 development results

## Result

The atomic-observation substrate is implemented and usable for development demonstrations. It is not ready to be called validated.

- observation schema: implemented;
- broad evidence-zone selector: implemented;
- provider-neutral semantic contract: implemented;
- deterministic provenance/entity/timing validator: implemented;
- 36-case contaminated review replay: completed;
- adversarial substrate tests: implemented;
- event-family mapper: deliberately absent;
- dimensions, scores and predictions: deliberately absent.

The strongest architectural result is that 24 reviewed factual observations rejected or left ambiguous by family-first 0.3.6 can pass through the observation-first substrate without being forced into an event family. Exact evidence-span validation succeeded for all 36 replay cases.

The biggest remaining weakness is unmeasured live semantic extraction quality. The development provider replays the AI-assisted answers to test the contract. A new, preregistered and genuinely independent validation design is required before claiming that new documents can be extracted reliably.

The UI now renders selected accepted development observations on a real-company development profile, explicitly labelled `DEVELOPMENT EXTRACTION — NOT YET VALIDATED`, while the existing Affirm profile continues to show trusted careers collector data.

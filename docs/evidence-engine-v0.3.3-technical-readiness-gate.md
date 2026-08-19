# Evidence Engine 0.3.3 technical-readiness gate

Frozen before the final unseen rerun. This is an engineering gate, not the formal Evidence Engine 0.3 Model 2 gate.

Evidence Engine 0.3.3 may be frozen for formal blinded review only if:

- new unseen accepted-event precision is at least 85%;
- severe false positives are zero;
- target/third-party attribution errors are zero;
- the rerun of the 0.3.2 unseen set has no more than three obvious false positives;
- the protected six-document benchmark has zero missed reviewed events and zero severe disagreements;
- the five-document historical/table fixes do not materially regress;
- duplicate events remain zero or near-zero;
- supported current target-company, segment and subsidiary events remain detectable.

At least 90% precision is preferred, but it must not be achieved by indiscriminate suppression. The threshold will not be changed after final unseen results are calculated.

Possible decisions are `TECHNICALLY READY FOR FORMAL REVIEW` or `NOT TECHNICALLY READY FOR HUMAN REVIEW`. Official Model 2 readiness remains `NOT READY` in either case.

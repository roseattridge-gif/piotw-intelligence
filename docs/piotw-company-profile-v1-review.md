# PIOTW company profile v1 review

## Product-quality changes

The internal `/intelligence/affirm` profile now answers five questions in order:

1. **What is happening?** It states that the only supported current company evidence is careers activity.
2. **What changed?** It shows vacancy state/change and separately reports postings absent once, confirmed closures and reopenings.
3. **Where is there evidence?** Workforce & Capability is marked observed; seven dimensions show `INSUFFICIENT OBSERVED DATA`.
4. **Why does PIOTW say this?** Observations expose source links; the subordinate debug view exposes observation IDs, source hashes, timestamps and collector version.
5. **What is unknown?** Missing source families, unresolved procurement, sparse dimensions and unvalidated product capabilities are explicit.

The hierarchy now separates “Available now — factual company evidence” from “Not yet validated — scores and predictions.” The page never displays an empty dimension as though it were zero and never attaches unresolved procurement records.

## Remaining product limitations

- Only one source family currently produces company-attached evidence for Affirm.
- Two careers snapshots support change but not robust trend/acceleration claims.
- No accepted issuer-report or procurement event is available for this company snapshot.
- The page is an internal inspection surface, not a public product claim.


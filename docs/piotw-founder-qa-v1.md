# PIOTW founder QA v1

This is a review guide for the current factual-intelligence prototype. It is not a test of a score, rating or prediction: none is present in this interface.

## Open PIOTW

1. Open Terminal.
2. Run:

   ```bash
   cd "/Users/roseattridge/Documents/ChatGPT/PIOTW MVP CODEX"
   make founder-demo
   ```

3. Leave that Terminal window open.
4. Open <http://127.0.0.1:3000/intelligence/brief>.

## Suggested 15-minute review journey

1. Start at **Portfolio brief**: <http://127.0.0.1:3000/intelligence/brief>.
2. Open **Watchlist** and try one sort and one filter: <http://127.0.0.1:3000/intelligence>.
3. Open **Recent changes** and filter to a company or source family: <http://127.0.0.1:3000/intelligence/changes>.
4. Open **Compare**, deselect Anduril, select Tesla, then apply the comparison: <http://127.0.0.1:3000/intelligence/compare>.
5. Open **Affirm** to inspect two careers snapshots, lifecycle states and retained vacancy evidence: <http://127.0.0.1:3000/intelligence/affirm>.
6. Open **Tesla** to inspect the development-only issuer observations and expand **View exact evidence**: <http://127.0.0.1:3000/intelligence/tesla>.
7. Open **Anduril** to see how the product exposes a failed source and insufficient evidence: <http://127.0.0.1:3000/intelligence/anduril>.
8. Finish with Tesla's **Evidence brief**: <http://127.0.0.1:3000/intelligence/tesla/brief?period=all>.

These companies were chosen to demonstrate functionality, not because PIOTW considers them important, healthy or risky.

- **Affirm** has a clean two-snapshot careers history with persisted roles and unconfirmed absences.
- **Tesla** is the only profile currently carrying the four development issuer-document observations, so it is the clearest evidence/provenance example.
- **Anduril** demonstrates an honest source-failure and insufficient-data state.

## Portfolio brief

- Is it immediately obvious what this page is telling me?
- Can I tell the difference between a new observation and a careers lifecycle change?
- Would I know what changed without reading every card?
- Is anything competing for attention unnecessarily?
- Are the data gaps prominent enough?
- Does the “no score, no ranking, no prediction” boundary feel clear or repetitive?

## Watchlist

- Can I understand the difference between companies?
- Do I know what I should click next?
- Do the sort and filter controls help me navigate, or feel like plumbing?
- Is the information useful or merely technical metadata?
- Is the source-attention state understandable without explanation?
- Does starting with Anduril's missing data help honesty, or obscure the useful records?

## Recent changes

- Are these changes understandable?
- Are they too granular or repetitive?
- Would I care about persisted-role counts, or only new/absent/closed roles?
- Are the filters the right ones?
- Is it clear that “absent once” is not a confirmed closure?
- Can I tell why each item is present and where its evidence lives?

## Compare

- Does comparing companies this way help?
- What am I actually learning from Affirm beside Tesla?
- Is “Unavailable” handled clearly and fairly?
- Are any rows falsely inviting a better/worse interpretation?
- What factual attributes are missing?
- Would the comparison become more useful after histories are deeper?

## Company

- Can I understand the operational picture in 60 seconds?
- Does **What changed?** work?
- Is the careers information meaningful at only two snapshots?
- Are the source gaps honest and understandable?
- Are the eight dimensions useful as a visibility map, or mostly empty furniture?
- Is the page too long for the amount of evidence currently available?

## Evidence

- Can I easily understand why PIOTW believes a fact?
- Does expanding **View exact evidence** answer the question directly?
- Is the distinction between observation, evidence and source clear?
- Is provenance helping or overwhelming?
- Which technical fields belong in the main page, and which belong only in an audit view?
- Is “development extraction — not yet validated” prominent enough?

## Brief

- Would I send this to somebody?
- Is it clear what period it covers?
- Does the evidence-reference structure work on screen and when printed?
- Is the source-hash detail useful in a shareable brief or only internally?
- What would make this more decision-useful without adding an unvalidated score?

## Final founder reaction

Write down reactions before discussing the next sprint:

- **What feels like PIOTW?**
- **What does not feel like PIOTW?**
- **What is missing?**
- **What should be removed?**
- **What did I expect to see but could not find?**
- **What would I show a prospective customer today?**
- **What would I refuse to show them yet?**

## Current visible limitations

- Careers history is only two snapshots for 11 companies; this is early longitudinal evidence, not a trend.
- Anduril's careers source has failed and therefore shows no careers observations.
- Resolved company-level procurement evidence is not yet available in the interface.
- Issuer-document observations are development-only and currently attached only to Tesla.
- The eight dimensions are visibility placeholders; they are not scored.
- No benchmark, rating, Pressure/Expansion score or prediction is shown.
- Some provenance is intentionally technical and may feel heavy; that is a founder-review question, not a claim that the current balance is final.

## Screenshot reference

The verified screenshots are in `output/founder-review-v1/screenshots/`:

- `01-portfolio-brief.png`
- `02-watchlist.png`
- `03-recent-changes.png`
- `04-compare.png` — Affirm compared with Tesla
- `05-affirm-company.png`
- `06-tesla-evidence.png` — exact evidence expanded
- `07-anduril-data-gap.png`
- `08-printable-brief.png`


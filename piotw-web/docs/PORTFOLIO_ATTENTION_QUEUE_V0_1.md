# Portfolio Attention Queue v0.1

## Outcome

`/portfolio` is the first founder-facing portfolio attention queue prototype. It presents a clearly labelled 20-company simulated portfolio and helps an operating or investment professional decide where to look first, why, and what to validate next.

This is product-validation software, not production portfolio ingestion and not a validated scoring or prediction system.

## Product semantics

- The first three companies are fixed, deliberately differentiated priorities: Northstar Industrial (`Investigate now`), Harbour Home Products (`Watch closely`) and Vertex Care Services (`Validate`).
- `rank` is explicit deterministic demonstration ordering. It is not calculated from an opaque composite score.
- Attention priority means the expected value of scarce operating-team attention. It does not mean worst company, probability of failure, operational health, evidence confidence or confirmed financial loss.
- Direction, velocity, potential impact, evidence confidence, urgency and thesis relevance remain separate fields.
- `UNKNOWN` and `WITHHELD` are visible states and are never converted to zero.
- Improving companies have routine urgency and appear as `Pressure easing` or `No immediate action`.

## Architecture and reuse

- `types/portfolio-attention.ts` defines the smallest portfolio-facing model.
- `data/portfolio-attention-demo.ts` is an isolated fictional fixture. It does not enter production-shaped data paths.
- `lib/data/portfolio-attention.ts` is the frontend adapter boundary.
- `components/portfolio-attention-queue.tsx` owns filters, priority cards, the remaining-company register and expandable validation detail.
- `app/portfolio/page.tsx` supplies the server-rendered route.
- The first priority routes to the existing `/north-star/northstar-industrial` company journey.
- The public homepage remains intact and now has a portfolio CTA. The global navigation also exposes `/portfolio`.
- Existing typography, colour tokens, semantic labels and responsive conventions are reused. No dependency or backend migration was added.

## Verification

- Portfolio tests: 7/7 passed.
- Complete web test suite: 42/42 passed.
- TypeScript: passed with `tsc --noEmit`.
- ESLint: passed.
- Production build: passed using Next.js 16.3.1 with webpack; `/portfolio` was prerendered as a static route. The default Turbopack path cannot bind its local CSS worker port in this managed environment.
- Desktop browser: 1440 × 1000, all three priorities aligned at the top of the queue, 17 remaining rows, filters correct, Northstar navigation correct, no console errors, and document width 1440/1440.
- Mobile browser: 390 × 844, responsive stack readable, priority card legible, filters fit the viewport, no console errors, and document width 390/390.
- Existing `/company/northstar-industrial` and `/company/travis-perkins/x-ray` routes rendered correctly.
- Native controls have accessible labels; attention state and direction use text and symbols in addition to colour.

Screenshots:

- `docs/portfolio-attention-desktop-viewport.png`
- `docs/portfolio-attention-mobile-top.png`
- `docs/portfolio-attention-mobile-priorities.png`

## Limitations and buyer questions

- All portfolio companies and values are fictional demonstration fixtures.
- Only Northstar has a complete linked company journey.
- The prototype does not ingest portfolio data, monitor continuously, complete an investment re-underwrite or prove commercial demand.
- Buyer testing must determine whether the top-three hierarchy is understood without coaching, whether `attention` is preferable to `risk`, which evidence threshold is credible, and whether the recommended management question is specific enough to trigger action.
- Buyers must also clarify who owns triage, how often the queue is reviewed, what would dismiss an alert, and when internal data should override the outside-in view.

## Highest-value next test

Run five uncoached 15-minute sessions with PE operating partners. Ask each participant to identify the top three companies, explain why Northstar ranks first, choose the next management action, and distinguish observation, inference, hypothesis and withheld output. Measure time-to-correct-priority and whether the participant would place the item on the next operating-review agenda.

## Scientific boundary

The parallel physical-row segmentation programme remains `EXTERNAL_REVIEW_REQUIRED`. No blinded truth, frozen prediction, protected outcome, scientific model or evidence gate was accessed or changed by this sprint.

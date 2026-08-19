# PIOTW web development rules

- Evidence provenance must never be hidden. Show unavailable fields as unavailable; never fill gaps by invention.
- Evidence, interpretation and prediction are different semantic objects and must remain visually and structurally separate.
- Never present inference as company fact. Prefer “evidence suggests”, “public disclosures indicate” and “observed”.
- Do not invent model scores, probabilities, evidence citations, source excerpts, dates or page numbers.
- Prediction UI renders only when a validated prediction object is explicitly supplied.
- The analytical and Evidence Engine logic lives outside this repository. Do not recreate it here.
- UI code reads intelligence through `lib/data`; do not couple components directly to fixtures.
- Maintain strict TypeScript safety and favour small reusable components.
- Use colour to communicate meaning, preserve keyboard access, and keep mobile layouts usable.
- Run lint, typecheck, tests and a production build before completing substantial changes.

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

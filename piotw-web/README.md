# PIOTW web

The first front-end MVP for **PUT IT ON THE WALL**, an outside-in operational-intelligence product. It presents public-company evidence, operational signals, interpretations and—only when validated data exists—predictions as distinct, traceable concepts.

This repository contains presentation code and development-safe mock data only. It does not contain or recreate PIOTW's analytical models.

## Run locally

Requires Node.js 22.6 or later and npm. (The application itself follows Next.js's Node 20.9 minimum; Node 22.6 is specified so the dependency-free TypeScript tests can use Node's built-in type stripping.)

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). For full verification:

```bash
npm run lint
npm run typecheck
npm test
npm run build
npm start
```

## Routes

- `/` — restrained landing page and local company search
- `/company/northstar-industrial` — company operational brief
- `/company/northstar-industrial/evidence` — filterable Evidence Wall and provenance drawer
- `/company/northstar-industrial/timeline` — filterable operational timeline
- `/company/northstar-industrial/documents` — analysed source library

## Structure and data boundary

- `app/` — Next.js App Router pages and global styles
- `components/` — reusable product and design-system components
- `types/` — strict intelligence-domain types
- `data/` — explicitly labelled development fixtures
- `lib/data/` — asynchronous repository/service boundary
- `tests/` — lightweight data-boundary tests

Pages and components do not import fixture data. They use functions in `lib/data/companies.ts`, such as `searchCompanies`, `getCompanyBySlug`, `getCompanyEvidence`, `getCompanyTimeline` and `getCompanyDocuments`. To connect a backend later, replace those function bodies with HTTP/API calls while preserving their typed contracts.

Northstar Industrial plc is fictional. Its content demonstrates layout and interaction only; it is not real analytical output. No source excerpt, URL or prediction is invented.

## Deploy to Vercel

1. Create an empty GitHub repository named `piotw-web`.
2. From this directory, initialise Git if needed, commit the files and push the branch to GitHub.
3. In Vercel, choose **Add New → Project**, import the GitHub repository, and leave the detected framework as **Next.js**.
4. No environment variables, database or external services are required. Select **Deploy**.
5. Verify `/`, the four company routes above, navigation, filters and the evidence drawer on the generated preview URL.

Vercel will detect Next.js automatically. Future pushes to the connected production branch and pull requests will trigger deployments.

Intentionally deferred: database, API, Supabase, authentication, Stripe, subscriptions, alerts, admin tools, account management and real Evidence Engine integration.

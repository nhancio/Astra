# Astra admin

The private portal lives at https://astraadmin.web.app. Firebase Hosting serves `frontend/out-admin` and forwards `/api/**` to the existing `yell-ai-api` service in `asia-south1`. The customer site retains its separate `astra` target. Firebase's [multisite Hosting documentation](https://firebase.google.com/docs/hosting/multisites) describes this setup.

## Access

Use the admin key configured as `ADMIN_API_KEY` on Cloud Run. The initial production key is stored in the `astra-admin-api-key` Secret Manager secret. Its owner copy is in the gitignored `.runtime/astra-admin-access.key`, readable only by the local account. Do not commit or share it. The portal holds the entered key in memory; reloading or signing out clears the session. Every admin API validates access on the backend.

To rotate access, create a new secret version and deploy a new Cloud Run revision resolving that version. Do not overwrite other service environment values. Keys shorter than 32 characters and the old public development key are rejected.

## Views and controls

- Overview: actual users, daily queries, active users, unexpired paid plans, flow outcomes and lifecycle distribution.
- Users: name/phone search, lifecycle and plan filters, pagination, setup step, interests, usage, connections, classified activity and external action history.
- Behavior: 7/30/90-day usage, classified intents/emotions, connected apps and tool-run outcomes.
- Model routing: configurable classifier, simple reply/fallback and complex reply models; measured calls, outcomes, mean latency and provider-reported token counts.
- Activity: paginated message flow metadata with outcome filters.
- Campaigns: existing campaign impressions, clicks, CTR, wallet budget and spend in INR.
- Settings: free/Pro/Max-or-Business limits, signup preview allowance, sponsored message switch, configured integrations and audit history. Billing products/prices and deployment credentials remain in their respective provider/server settings.

Lifecycle is derived, not manually overwritten: paid access takes priority; unregistered accounts remain preview; unfinished setup stays onboarding; completed/verified accounts with recent usage are active or dormant (7 UTC dates); completed setup without usage is ready. Expired paid plans display as free. Legacy Business and Max use the same configurable highest-tier limit.

Settings live in PostgreSQL `runtime_config`, with a revision checked on every save. Concurrent edits receive HTTP 409 and must reload. `admin_audit` records before/after values in the same transaction. Backend operations read shared overrides so saves apply across instances on the next request. The JSON classifier can select all three supported Gemini models; thinking is minimal for Lite and low for Flash. Complex calls have a 10-second first-attempt timeout, one fallback retry and a 20-second total generation budget.

Model telemetry and classification events start with this release; historical token counts, intent events and billing costs are not invented. Classification events contain intent/emotion metadata, not prompts or reply content. UTC is used for report dates and formatting. Model telemetry is best effort, with bounded writes so an analytics outage does not fail a successful reply.

## Build and verification

```sh
cd frontend
NEXT_PUBLIC_BACKEND_URL='' npm run build:sites
cd ../backend
ENVIRONMENT=test DATABASE_URL='sqlite+aiosqlite:///:memory:' BACKEND_DATABASE_URL='sqlite+aiosqlite:///:memory:' .venv/bin/python -m unittest discover -s tests
```

`build:sites` produces both `out/` and `out-admin/`. Admin output contains its root document, Next assets, brand icons and a robots exclusion; it does not publish the customer landing page as its entry point. Run `./deploy.sh` from the repository root for normal releases. It builds and deploys the full backend, binds the admin secret, verifies protected and authenticated admin access on the staged revision, and publishes both Hosting targets after validation. To deploy only a tested admin build:

```sh
firebase deploy --only hosting:admin --project yell-ai-nhancio --non-interactive
```

The first admin backend release is an overlay on the pinned production container, preserving existing billing and deployment settings while the separate Polar migration is in progress. Its compatibility source and deployment artifacts are retained under gitignored `.runtime/admin-release*` and `.runtime/admin-compatibility/`. Subsequent normal source releases include the same admin modules.

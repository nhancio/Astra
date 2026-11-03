# Astra admin portal implementation plan

**Goal:** Operate Astra from astraadmin.web.app using the existing FastAPI, PostgreSQL and Next.js stack.

**Design:** A separate Firebase Hosting target serves the admin screen at its root. Every API requires the existing server-side admin key, held only in browser memory. Read models expose actual users, onboarding stages, usage, connector/tool activity and delivery logs. Durable, validated configuration controls model roles and usage limits across backend instances, with optimistic concurrency and an audit trail. Model-call telemetry starts at release; historical token/cost data is not fabricated.

**Constraints:** Preserve existing user edits and app routes. Add no dependencies. Never return deployment secrets. No destructive user operations. Lifecycle stages are derived from actual onboarding, subscription and usage records. Dates in analytics are UTC. Operational settings apply on the next request; credentials stay in deployment configuration.

- [x] Add regression checks for admin authentication, lifecycle analytics, config validation/concurrency, and live routing/usage overrides.
- [x] Add configuration, audit and model-call tables; authenticated APIs for overview, users/details, behavior, routing, settings, logs, campaigns and integrations.
- [x] Connect the actual Gemini and usage services to durable config; collect model latency, outcome and token counts.
- [x] Build responsive admin UI with accessible navigation, filters, user drilldown, editable routing/settings and error/empty/loading states.
- [x] Add isolated Hosting target and root rewrite; verify backend suite, frontend build and hosting configuration.
- [x] Deploy only tested backend/admin artifacts if credentials and target are available; smoke-test access gates and live APIs.

**Verification:** 122 current backend tests, 116 isolated production compatibility tests, 15 deployment workflow checks, six frontend entry-flow checks, production build, local desktop/mobile browser flows, and real production admin login/API/routing checks passed. The separate new Python session-entry browser suite requires Python Playwright and its dedicated dev server; it was not used for admin verification.

**Released:** Firebase admin target at https://astraadmin.web.app; Cloud Run revision `yell-ai-api-00077-lih`, overlaid on `yell-ai-api-00075-wic` to retain the concurrent legal release. Admin key remains in Secret Manager, with a local owner copy under `.runtime/`.

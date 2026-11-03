# Polar subscriptions

Astra Free is $0. Astra Pro is $1/month with 10 messages/day; Astra Max is
$5/month with 30 messages/day. Existing `business` account tiers and links
continue to work as Max. The free allowance is 5 messages/day.

Production products created in the existing Nhancio Polar account:

| Plan | Product ID | Monthly USD amount |
| --- | --- | --- |
| Astra Pro | `ab3e3003-c953-4dd7-a114-c49364006bac` | 100 cents |
| Astra Max | `a5f4bf8e-af33-4443-ac9e-21014ec58d17` | 500 cents |

Both products were checked against Polar's live checkout API; returned amounts
were 100 and 500 USD cents. No payment was made.

The ignored root `.env` contains the reused `POLAR_ACCESS_TOKEN`, product IDs,
and a dedicated Astra `POLAR_WEBHOOK_SECRET`. No secrets belong in the frontend.
`POLAR_SERVER=sandbox` selects the sandbox API, which requires its own token,
products and webhook secret. API requests are pinned to `2026-10`.

Website buyers sign in before checkout. The backend binds checkout metadata to
their verified WhatsApp phone; incoming WhatsApp upgrade commands use the
sender's number. Billing email is collected by Polar. Redirect query parameters
cannot choose the account or grant a plan.

The return endpoint fetches the checkout from Polar, checks its succeeded
status, then fetches the subscription. Webhooks verify the Standard Webhooks
signature and five-minute timestamp tolerance before refreshing the current
subscription from Polar. Only Astra's configured product IDs and Astra-tagged
metadata can affect access. Access expires at Polar's exact billing period end;
replayed events do not add another month. A new `polar_subscriptions` table is
created by the existing `ensure_tables()` startup path; existing users need no
column migration.

## Release configuration

The app source has not been deployed. The existing deploy script preserves cloud
environment settings and does **not** upload local `.env`. Before deploying,
configure these backend-only environment values or secret references on Cloud Run:

- `POLAR_ACCESS_TOKEN`
- `POLAR_WEBHOOK_SECRET`
- `POLAR_PRO_PRODUCT_ID`
- `POLAR_MAX_PRODUCT_ID`
- `POLAR_SERVER=production`
- `PRO_PRICE_CENTS=100`, `MAX_PRICE_CENTS=500`
- `FREE_DAILY_LIMIT=5`, `PAID_DAILY_LIMIT=10`, `MAX_DAILY_LIMIT=30`

Remove obsolete Razorpay environment references from the service. Do not revoke
shared Razorpay credentials belonging to other products.

The dedicated Astra webhook is staged at
`https://tryastra.web.app/payment/webhook`, endpoint ID
`93379c6f-c0a6-4ea5-a4f5-ab58de757dd4`. It currently has no subscribed events,
so the existing production backend will not receive incompatible deliveries.
After deploying and checking the new backend, set its events in the Polar
dashboard (API version `2026-10`, raw format) to:

- `order.paid`
- `subscription.active`
- `subscription.updated`
- `subscription.canceled`
- `subscription.uncanceled`
- `subscription.revoked`

Keep the endpoint URL and `APP_URL` aligned if the public domain changes.
Use [Polar's webhook delivery view](https://polar.sh/docs/integrate/webhooks/delivery)
to confirm successful deliveries and replay any failed delivery after a release.

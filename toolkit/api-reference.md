# Gumroad API v2 — complete reference

Verified 2026-10-14 from the official docs at `https://gumroad.com/api`.
Base: `https://api.gumroad.com/v2`. Auth: `Authorization: Bearer <token>` or `-d "access_token=<token>"`.
Every response: JSON. Success: `{"success": true, ...}`. Error: `{"success": false, "message": "..."}`.

## Products

### GET /products
List all products for the authenticated user. `sales_count`/`sales_usd_cents` need `view_sales` or `account`.
```bash
curl https://api.gumroad.com/v2/products -d "access_token=TOKEN" -X GET
```
Product object: `id`, `name`, `description`, `price` (cents), `currency`, `formatted_price`, `category` (path), `category_label`, `taxonomy_id`, `tags[]`, `custom_summary`, `custom_permalink`, `custom_receipt`, `custom_fields[]`, `customizable_price`, `deleted`, `max_purchase_count`, `preview_url`, `require_shipping`, `subscription_duration`, `published`, `short_url`, `thumbnail_url`, `file_info{}`, `purchasing_power_parity_prices{CC:cents}`, `is_tiered_membership`, `recurrences[]`, `variants[{title, options[{name, price_difference, purchasing_power_parity_prices, is_pay_what_you_want, recurrence_prices}]}]`.

### GET /products/:id
Same shape wrapped as `{"success":true,"product":{...}}`, plus `custom_html`.

### POST /products — create (publishes immediately by default)
Params: `draft`, `published`, `native_type` (`digital` default, `course`, `ebook`, `membership`, `bundle`, `coffee`, `call`, `commission` — immutable), `name`*, `description` (HTML), `custom_permalink`, `price`* (cents), `price_currency_type` (ISO, defaults to account currency), `subscription_duration` (`monthly`/`quarterly`/`biannually`/`yearly`/`every_two_years`), `customizable_price`, `suggested_price_cents`, `max_purchase_count`, `category` (path) XOR `taxonomy_id`, `tags[]`, `custom_summary`, `refund_period` (`inherit`/`none`/`7`/`14`/`30`/`183`), `refund_fine_print`, `rich_content[{id,title,description}]` (ProseMirror doc), `files[file_url]`. Covers via `POST /products/:id/covers`, thumbnail via `POST /products/:id/thumbnail`.
If publishing is blocked (email unconfirmed / no payout method) it saves as a **draft** and the response carries a `warning`; publish later with `POST /v2/products/:id/enable` (doc: `PUT`). Requires `edit_products` or `account`.
```bash
curl https://api.gumroad.com/v2/products -d "access_token=TOKEN" -d "native_type=ebook" -d "name=Guide" -d "price=2000" -X POST
```

### PUT /products/:id — update (same params); DELETE /products/:id
### PUT /products/:id/enable — publish a draft · PUT /products/:id/disable — unpublish

### GET /products/:id/reviews — paginated public reviews
Only reviews with a written message (or approved video). Star-only ratings count toward `average_rating` but aren't returned. Params: `page_key`. Item: `id`, `rating`, `message`, `created_at`, `purchase_id`, `rater_name`, `response{message, created_at}`.

## Public endpoints (no token)

- `GET /l/:permalink.json` — public product page.
- `GET https://[username].gumroad.com/.json` — public profile.

## Categories

`GET /categories` → `[{id, name, label, path, parent_id}]`. Use `path` (e.g. `design/ui-and-web/figma`) or `taxonomy_id` as the product `category`.

## Files (S3 multipart, 4 steps, max 20 GB)

1. `POST /files/presign` (`filename`, `file_size` bytes; requires `edit_products`) → `{success, upload_id, key, file_url, parts:[{part_number, presigned_url}]}` — one part per 100 MB.
2. `PUT` each part to its presigned URL; capture the response **`ETag`** header.
3. `POST /files/complete` (`upload_id`, `key`, `parts` = `[{part_number, etag}]`).
4. Attach `file_url` as `files[file_url]` on product create/update. Optional `client_id` (CLI: `cli-upload-…`) → response returns `file_id_mappings` client_id → ProductFile id.

`POST /files/abort` (`upload_id`, `key`) → `status`: `accepted` (abort again, in-flight parts may still land) | `already_gone` (done, stop).

## Covers & thumbnails
- `POST /products/:product_id/covers` · `DELETE /products/:product_id/covers/:id`
- `POST /products/:product_id/thumbnail` · `DELETE /products/:product_id/thumbnail`

## Media library
- `GET /media` · `POST /media` · `DELETE /media/:id` — **dedicated scope required** (an `account`-scope token is refused).

## Variant categories & variants
- `GET/POST /products/:product_id/variant_categories` · `GET/PUT/DELETE .../variant_categories/:id`
- `POST /products/:product_id/variant_categories/:variant_category_id/variants` · `GET/PUT/DELETE .../variants/:id`
- Variant option: `name`, `price_difference` (0 for tiered membership options), `purchasing_power_parity_prices`, `is_pay_what_you_want`, `recurrence_prices{ <recurrence>: {price_cents, suggested_price_cents, purchasing_power_parity_prices} }`.

## Offer codes
- `GET /products/:product_id/offer_codes` · `GET .../offer_codes/:id`
- `POST /products/:product_id/offer_codes` — `name`, `amount_off`, `offer_type` (`cents` default | `percent`), `max_purchase_count`, `minimum_amount_cents`, `universal`
- `PUT/DELETE .../offer_codes/:id`
Object: `id`, `name`, `amount_cents` OR `percent_off`, `max_purchase_count`, `universal`, `times_used`.

## Emails (audience broadcasts — `edit_emails` or `account`)
- `GET /emails` (`type`: published/scheduled/draft; `page_key`) · `GET /emails/:id` · `DELETE /emails/:id`
- `POST /emails` — `subject`, `body` (HTML), `audience` (`all`/`audience`/`customers`/`seller`/`followers`/`follower`/`produ…`), `publish` (true sends immediately / draft)
- `POST /emails/:id/preview` · `POST /emails/:id/send` · `POST /emails/:id/schedule` (`send_at` ISO-8601 UTC) · `POST /emails/:id/unschedule`
Object: `id`, `subject`, `message`, `audience_type`, `product_id`, `state`, `published_at`, `scheduled_at`, `send_emails`, `shown_on_profile`, `audience_count`, `recipients_count`, `url`, `created_at`, `updated_at`.

## Workflows (automated sequences — `edit_emails` or `account`)
- `GET /workflows` · `GET /workflows/:id` (includes `emails[]` steps + stats) · `POST /workflows/:workflow_id/emails`
- Email step params: `subject`, `message`, `delay: {amount, unit}`. Step stats: `sent_count`, `open_count`, `open_rate`, `click_count`, `click_rate`.
- Workflow: `id`, `name`, `audience_type`, `trigger`, `product_id`, `variant_id`, `state`, `send_to_past_customers`, `emails_count`, `filters` (e.g. `{"paid_more_than": "20"}`).

## Custom fields
- `GET /products/:product_id/custom_fields` · `POST .../custom_fields` (`name`, `required`)
- `PUT/DELETE .../custom_fields/:name` (`required`; name URL-encoded, e.g. `phone%20number`)

## User
- `GET /user` · `GET/PUT /user/custom_html` (`custom_html`) · `POST /user/preview_custom_html`
- `GET/PUT /refund_policy` — `refund_policy_period` (`inherit`/`none`/`7`/`14`/`30`/`183`), `refund_fine_print`

## Resource subscriptions (API-driven webhooks — needs `view_sales`)
`PUT /resource_subscriptions` (`resource_name`, `post_url`) · `GET /resource_subscriptions` · `DELETE /resource_subscriptions/:id`
Resources (8): `sale`, `refund`, `dispute`, `dispute_won`, `cancellation`, `subscription_updated` (tiered memberships upgrade/downgrade), `subscription_ended` (failed payment, cancellation, or fixed duration ended — fires at actual end, not at cancellation request), `subscription_restarted`.

## Sales (`view_sales`)
`GET /sales` — params: `after`, `before` (`YYYY-MM-DD`), `product_id`, `email`, `order_id`, `name`, `license_key`, `page_key`.
Sale object: `id`, `email`, `seller_id`, `timestamp`, `daystamp`, `created_at`, `product_name`, `product_id`, `product_permalink`, `price`, `gumroad_fee`, `tax_cents`, `shipping_cents`, `variants_price_cents`, `access_revoked`, `variants{}`, `custom_fields{}`, `order_id`, `purchaser_id`, `is_recurring_billing`, `subscription_id`, `subscription_duration`, `formatted_display_price`, `formatted_total_price`, `currency`, `utm_source`/`utm_medium`/`utm_campaign`, `referrer`, `card{visual, type}`, `product_rating`, `reviews_count`, `average_rating`, `discover_fee_charged`, `is_gift_sender_purchase`, `is_gift_receiver_purchase`, `paid`, `disputed`, `dispute_won`, `chargedback`, `partially_refunded`, `amount_refundable_in_currency`, `can_contact`, `is_following`, `is_product_physical`, `require_shipping`.
- `GET /sales/:id`
- `PUT /sales/:id/refund` (`amount` cents → partial; omit → full) — `edit_sales`
- `PUT /sales/:id/mark_as_shipped` (`tracking_number`) — `mark_sales_as_shipped`
- `POST /sales/:id/resend_receipt` — `edit_sales`
- `PUT /sales/:id/revoke_access` · `PUT /sales/:id/undo_revoke_access` — `edit_sales`

## Subscribers (`view_sales`)
`GET /products/:product_id/subscribers` — `email` filter, `paginated` (100/page, default false), `page_key`.
Subscriber: `id`, `product_id`, `product_name`, `user_id`, `user_email`, `purchase_ids[]`, `created_at`, `user_requested_cancellation_at`, `charge_occurrence_count`, `recurrence`, `cancelled_at`, `ended_at`, `failed_at`, `free_trial_ends_at`, `license_key`, `status` (`alive`/`payment_method_update_required`/`pending_cancellation`/`pending_failure`/`failed_payment`/`fixed_subscription_period_ended`/`cancelled`).
`GET /subscribers/:id`

## Licenses
- `POST /licenses/verify` — **no OAuth app/token needed.** Params: `product_id`, `license_key`, `increment_uses_count` (default true). Returns `{success, uses, purchase{...}}` with the full purchase object (`email`, `price`, `gumroad_fee`, `currency`, `quantity`, `order_number`, `sale_id`, `sale_timestamp`, `variants`, `license_key`, `is_multiseat_license`, `ip_country`, `recurrence`, `refunded`, `disputed`, `dispute_won`, `chargebacked`, `subscription_ended_at`, `subscription_cancelled_at`, `subscription_failed_at`, `custom_fields[]`, `referrer`, `discover_fee_charged`, ...). 404 + envelope when the license doesn't exist for the product.
- `PUT /licenses/enable` · `PUT /licenses/disable` · `PUT /licenses/decrement_uses_count` · `PUT /licenses/rotate` — all take `product_id` + `license_key` (token required).

## Payouts (`view_payouts`)
`GET /payouts` · `GET /payouts/:id` · `GET /payouts/upcoming`

## Tax forms & earnings (`view_tax_data`, US sellers, tax center enabled)
- `GET /tax_forms` (`year`) → `[{tax_year, tax_form_type: us_1099_k|us_1099_misc, filed_at}]`
- `GET /tax_forms/:year/:tax_form_type/download` → **raw PDF** (`Content-Type: application/pdf`)
- `GET /earnings` (`year`, required) → `{success, year, currency, gross_cents, fees_cents, taxes_cents, affiliate_credit_cents, net_cents}` (fully-refunded sales excluded)
- `GET /payouts/:id` also breaks down `fees`, `refunds`, `chargebacks`, `taxes` rows per purchase (`type`: Sale/Full Refund/Chargeback/PayPal Payouts, `sale_price`, `gumroad_fees`, `net_total`).

## Fees (live from gumroad.com/pricing)
- **Direct sales (your profile/links/own site): 10% + $0.50** per transaction.
- **Discover marketplace: 30%** — charged when a **new** customer finds and buys via Discover.
- No monthly fee. **Merchant of Record since 2025-01-01**: Gumroad collects/remits all sales tax worldwide (VAT/GST); seller tax settings were disabled; CA resellers use Gumroad's resale certificate PDF.

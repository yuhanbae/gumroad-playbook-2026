# Gumroad API v2 — Field Notes & Fixes

This repo is the toolkit that ships with *The Gumroad Playbook 2026*.
If you hit an API behavior that isn't documented in `api-reference.md`,
open a PR here with:

1. The exact request (method, path, body)
2. The exact response
3. Date + API version

Verified gotchas so far (2026-10-14):

- File attach: only `files[][url]=<fresh presign URL>` works (repeated keys, full replacement). `files[file_url]`, `files[0]`, JSON lists, and resubmitting by `files[][id]`+URL all fail or silently drop files.
- `/files/complete` parts: repeated literal keys `parts[][part_number]` / `parts[][etag]` — nested `parts[0][...]` 400s.
- Cover/thumbnail `url` must be server-fetchable: the S3 presign URL from `/files/presign` is 403 to Gumroad's fetcher — host the image on a public URL (raw.githubusercontent.com etc.). Thumbnail must be square.
- `GET /products` product object has no `permalink` field — use `short_url`/`landing_url`.
- Publishing is blocked account-side until a payment method (bank/PayPal) is connected; the API has no payment-method endpoint.
- `gum.co/<slug>` 301s to `app.gumroad.com` (JS shell) — use `https://<username>.gumroad.com/l/<slug>` in links.

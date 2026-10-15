# Reddit — Cross-Post Drafts

## 1. r/SideProject (best fit)

**Title:** I wrote a 14-chapter Gumroad operating manual and shipped it with a Python API toolkit that published the book itself — free tripwire included

**Body:**

I've been building automations on Gumroad's v2 API and noticed most
of the Gumroad content out there is 2019-era blog posts describing
a dashboard that no longer matches the product. Fees changed,
Discover eligibility changed, tax handling moved to
merchant-of-record in 2025, and the v2 API (81 endpoints) quietly
became the only sane way to run the business as an automation.

So I wrote a book: 14 chapters, verified line-by-line against the
live API (api.gumroad.com/v2) and the open-source codebase
(github.com/antiwork/gumroad). When it says the fee is 10% + 50¢
direct / 30% via Discover for new customers, that's the fee on the
pricing page today.

It ships with a stdlib-only Python toolkit that's the book's proof
of concept — the publish_product.py in it is the exact pipeline
that created, uploaded, and published this very book.

The toolkit's been getting API gotchas documented that most
tutorials don't cover:
- File attach: only `files[][url]=<fresh presign URL>` works
  (repeated keys, full replacement). The other documented formats
  silently drop files or 400.
- `/files/complete` needs `parts[][part_number]` / `parts[][etag]`
  as repeated literal keys, not nested-hash form
- Cover/thumbnail must be a server-fetchable URL (presigned S3
  returns 403 to Gumroad's fetcher — host on GitHub raw or similar)
- `POST /v2/licenses/verify` works with no OAuth application at
  all — the licensing primitive for software sellers

$29 (code LAUNCH50 for 50% off for the launch period).
Free tripwire: "The 5-Line Check" — a 10-minute checklist + 5
one-liner Python scripts that tell you exactly why your Gumroad
account can't take real money, or prove it's ready.

**Links**
- Free tripwire: https://yuhanbreeze.gumroad.com/l/gyvimr
- Playbook: https://yuhanbreeze.gumroad.com/l/qmhyqi
- Landing + source: https://yuhanbae.github.io/gumroad-playbook-2026/

---

## 2. r/gumroad (if it exists) / r/Entrepreneur (if the side-project post gets heat)

Shorter, community tone:

**Title:** Just published a Gumroad operating manual that's verified against the live v2 API — free 5-minute checklist for account issues too

**Body:**

Most Gumroad content out there is 2019-era. Fees changed, Discover
rules changed, tax moved to merchant-of-record in 2025. I wrote a
14-chapter manual that's verified against the live v2 API last
week — every endpoint, every field, every gotcha I hit.

Free tripwire "The 5-Line Check" — 5 one-liners that tell you
exactly why your account can't take real money (or prove it's
ready). Runs on any Python 3.8+, including your phone.

Tripwire (free): https://yuhanbreeze.gumroad.com/l/gyvimr
Playbook ($29, LAUNCH50 for 50%): https://yuhanbreeze.gumroad.com/l/qmhyqi

---

## 3. r/webdev / r/python (toolkit angle)

**Title:** I built a stdlib-only Python client for Gumroad's full v2 API — all 81 endpoints, 4-step S3 file upload in one call, Ping webhook parser

**Body:**

The toolkit that ships with The Gumroad Playbook 2026 is MIT-
licensed and available on GitHub. No pip install, no dependencies,
runs on any Python 3.8+ (including Android/Termux).

- `gumroad.py` — full client: products, files, licensing, webhooks,
  sales, payouts, auto-pagination
- `publish_product.py` — the exact pipeline that published the book
- `sales_monitor.py` — cron-able sales poller with checkpoint state
- `ping_server.py` — webhook fulfillment with verify-before-fulfill
  pattern (Ping posts are unsigned, so we re-fetch via API before
  granting entitlements)
- `license_demo.py` — verify → enable → disable → decrement → rotate

Known gotchas documented in CONTRIBUTING.md:
- File attach: `files[][url]=<fresh presign URL>` only (repeated keys,
  full replacement). Other documented formats silently drop files.
- `/files/complete`: `parts[][part_number]` / `parts[][etag]` as
  repeated literal keys, not nested-hash form
- Cover/thumbnail: must be a publicly fetchable URL (presigned S3
  403s to Gumroad's fetcher)
- `GET /products` has no `permalink` field — use `short_url` /
  `landing_url`

Full docs + API reference in the repo. PRs welcome if you hit
something I haven't documented.

https://github.com/yuhanbae/gumroad-playbook-2026

---

## 4. r/indiehackers / r/startup (results + honest part)

**Title:** The honest part about Gumroad: it's a payment+delivery+tax engine, not a traffic engine. 90-day plan in the book I just published.

**Body:**

I wrote a 14-chapter operating manual for building a Gumroad
digital-product business in 2026, verified against the live v2 API.
The book is honest about what Gumroad actually is: a payment +
delivery + tax engine. Merchant-of-record since Jan 2025 (VAT/GST
handled, no registration required on your side). The reliable
money comes from a distribution channel you control — an email
list, a YouTube channel, a niche subreddit, SEO, or paid ads.

Chapter 14 is a 90-day plan built around that reality.

Free tripwire "The 5-Line Check": 5 one-liners that tell you
exactly why your account can't take real money, or prove it's
ready. 10 minutes, no dependencies.

Tripwire (free): https://yuhanbreeze.gumroad.com/l/gyvimr
Playbook: https://yuhanbreeze.gumroad.com/l/qmhyqi
(code LAUNCH50 for 50% off at launch)

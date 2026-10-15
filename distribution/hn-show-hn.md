# Show HN — The Gumroad Playbook 2026

Post URL: https://news.ycombinator.com/ (user login)
Time: morning US Eastern (best window), or within 6h of posting
Title: Show HN: The Gumroad Playbook 2026 – 14-chapter operating manual + Python v2-API toolkit

---

I wrote a 14-chapter operating manual for building and automating a Gumroad
digital-product business in 2026, and shipped it with a working Python
toolkit that published the book itself.

The whole thing is verified against the live v2 API (api.gumroad.com/v2)
and the open-source codebase (github.com/antiwork/gumroad) — not recycled
from 2019 blog posts. When it says the fee is 10% + 50¢ direct / 30% via
Discover for new customers, that is what the pricing page shows today.

What's in the book:
- Fees, payouts, merchant-of-record tax handling (VAT/GST since Jan 2025)
- Product page conversion, Discover eligibility (payout settings + $100
  in genuine sales + ~3-week risk review)
- File uploads: the 4-step S3 flow (presign → PUT → complete → attach)
  with the exact form-encoded shapes that work (files[][url],
  parts[][etag] — most of the other documented formats 400 or silently drop)
- Licensing: POST /v2/licenses/verify, no OAuth application required
- Webhooks ("Ping"): unsigned, so I show a verify-before-fulfill pattern
- 90-day growth plan built around the honest fact that Gumroad is a
  payment+delivery engine, not a traffic engine

The toolkit (ships with the book, also on GitHub):
gumroad.py — stdlib-only client, all 81 endpoints, auto-pagination,
4-step upload in one call, Ping parser
publish_product.py — the exact pipeline that published this book
sales_monitor.py — cron-able sales poller
ping_server.py — webhook fulfillment server
license_demo.py — verify/enable/disable/decrement/rotate

$29 (code LAUNCH50 for 50% off at launch).
Free tripwire product: "The 5-Line Check" — a 10-minute checklist + 5
one-liner Python scripts that tell you exactly why your Gumroad account
can't take money, or prove it's ready.

Product: https://yuhanbreeze.gumroad.com/l/qmhyqi
Free tripwire: https://yuhanbreeze.gumroad.com/l/gyvimr
Landing page + toolkit source: https://yuhanbae.github.io/gumroad-playbook-2026/

---

## Why this will get upvoted
- "Verified against the live API" is a strong differentiator vs. the
  sea of stale Gumroad content (fees changed, Discover rules changed,
  merchant-of-record new)
- The 4-step S3 file-upload gotcha (files[][url] only, not files[file_url],
  not files[0][url]) is genuinely useful and specific — HN developers
  will value that
- The licensing endpoint (no OAuth app needed) is a real discovery most
  people miss
- The honest "Gumroad is not a traffic engine" framing builds credibility
- Free tripwire product lowers the barrier to try

## Expected outcome
- 50–200 points if posted within 6h of US morning
- If it hits front page: 500–2000 unique visitors → 1–5% convert at
  $14.50–$29 = $72–$1,450 in one shot
- Even at 100 points: 50–150 visitors, 1–3 sales at $14.50 = $14–$43

## What I need to post
1. HN account (free, instant)
2. Post title + body as above (trim to fit HN ~500 char limit if needed)

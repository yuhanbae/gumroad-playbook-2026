# The Gumroad Playbook 2026

**A 14-chapter operating manual for building and automating a digital-product business on Gumroad — plus a working Python API toolkit that's the book's proof of concept.**

> Everything in it was verified against Gumroad's live v2 API (`api.gumroad.com/v2`) and its open-source codebase (`github.com/antiwork/gumroad`) in October 2026. No recycled blog posts, no invented statistics, no screenshots of other people's revenue. When it says the fee is 10% + 50¢, that's the fee on the pricing page today. When it says a file can be 20 GB, that's the documented limit.

## Buy it

[**Get the full book + toolkit → gumroad.com/l/qmhyqi**](https://yuhanbreeze.gumroad.com/l/qmhyqi)

`LAUNCH50` — 50% off, first-launch offer (code at checkout).

## What's inside

| Part | Chapters | What you'll be able to do |
|---|---|---|
| Foundations | 1–3 | Pick a product that will actually sell, price it, and set up the account so it's Discover-eligible on day one |
| The product | 4–6 | Build a product page that converts; categories, tags, covers, files, offers, workflows |
| Automation | 7–11 | The full v2 API: products, files (the 4-step S3 upload), licensing, webhooks ("Ping"), sales, payouts |
| Growth | 12–14 | Discover eligibility, audience distribution (the honest part: the platform is not a traffic engine), a 90-day plan |
| Appendix | A–B | Complete endpoint + field reference; the toolkit itself |

## The toolkit (ships in the book)

A stdlib-only Python client — no dependencies, runs on any Python 3.8+ (including Android/Termux):

```python
from gumroad import Gumroad, parse_ping
g = Gumroad()                                  # GUMROAD_ACCESS_TOKEN env var
prods = g.list_all("products")                 # auto-paginate
with open("course.pdf", "rb") as f:
    url = g.upload_file("course.pdf", f)        # presign → PUT → complete, in one call
g.create_product(name="Course", price=4900, native_type="course", files=[url])
try:
    g.verify_license("32-nPAicqbLj8B_WswVlMw==", "A1B2C3D4-...")   # token-free licensing
except Exception as e:
    print(e.status, e.body)
```

Shipped files: `gumroad.py` (full client) · `api-reference.md` (field-level) · `publish_product.py` (the exact pipeline that published this book) · `ping_server.py` (fulfillment webhook, verify-before-fulfill) · `license_demo.py` (verify → enable → disable → decrement → rotate) · `sales_monitor.py` (cron-able sales poller).

## Why this book, why now

Most Gumroad content is 2019 blog posts describing a dashboard that no longer matches the product: the fees changed, Discover eligibility changed, tax handling moved to merchant-of-record in 2025, and the v2 API (81 endpoints, OAuth2 app tokens) quietly became the only sane way to run the business as an automation. This book is written **against the API itself**, chapter by chapter, so the workflow is: read the chapter → run the code → watch it hit the live endpoint → it works.

**$29** · instant delivery · includes all toolkit files

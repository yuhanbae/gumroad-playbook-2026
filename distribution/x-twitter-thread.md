# X / Twitter — 6-Tweet Launch Thread

Handle: @yuhanbae (or your main account)
Best time: Tue–Thu, 9–11 AM US Eastern
Tag: #gumroad #indiehacker #buildinpublic

---

**1/6**

I just published The Gumroad Playbook 2026 — a 14-chapter operating
manual for building a digital-product business on Gumroad, verified
line-by-line against the live v2 API last week.

It ships with a working Python toolkit that published the book itself.

$29 (code LAUNCH50 for 50% off this week only). Free tripwire:
"The 5-Line Check" — 10-minute checklist that tells you exactly why
your Gumroad account can't take real money, or prove it's ready.

🔗 https://yuhanbae.github.io/gumroad-playbook-2026/

**2/6**

Most Gumroad content is 2019 blog posts describing a dashboard that no
longer exists. Fees changed. Discover eligibility changed. Tax handling
moved to merchant-of-record in 2025. The v2 API quietly became the
only sane way to run this business as an automation.

This book is written *against the API itself*. Read a chapter → run
the code → watch it hit the live endpoint. It works.

**3/6**

The thing most people don't know: the file-upload flow has one format
that works (files[][url] as repeated form fields) and five documented
formats that silently drop your files or 400. The /files/complete
endpoint needs parts[][etag], not parts[0][etag]. The cover endpoint
refuses presigned S3 URLs — you need to host the image on a public
URL first.

All of this is in the book. All of it is verified today, not
theoretical.

**4/6**

The licensing endpoint is the most underrated one:
POST /v2/licenses/verify takes a product_id and a license_key,
returns the license state, and works with no OAuth application
token at all. For anyone selling software on Gumroad and not using
it yet — this is your activation primitive.

**5/6**

Honest part, which the whole book is built around: Gumroad is a
payment + delivery + tax engine. It is not a traffic engine. Discover
will send you some discovery traffic, but the reliable money comes
from a channel you control. Chapter 14 is a 90-day plan built
around that reality.

**6/6**

If you're selling (or want to sell) digital products — templates,
presets, courses, fonts, 3D models, printables, a license key for
your app — the free tripwire takes 10 minutes and tells you
exactly what's blocking you from taking real money today.

Free: https://yuhanbreeze.gumroad.com/l/gyvimr
Full playbook: https://yuhanbreeze.gumroad.com/l/qmhyqi

---

## Pinned reply
Code LAUNCH50 (50% off, $14.50) is live for the first 2 weeks.
Instant delivery. The toolkit is MIT-licensed — fork it, ship with it,
tell me if you find an API gotcha I missed (open a PR on the repo).

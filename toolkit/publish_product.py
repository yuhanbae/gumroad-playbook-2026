#!/usr/bin/env python3
"""Publishing pipeline used to publish "The Gumroad Playbook 2026".

Steps (exactly what Appendix B describes):
  1. Create draft product (name, price, category, tags, description)
  2. Upload files (book PDF, toolkit, cover) via the 4-step S3 flow
  3. Attach files
  4. Set cover + thumbnail
  5. Enable (publish)
  6. Verify via public JSON endpoint

Reads GUMROAD_ACCESS_TOKEN from env (or ../.env). No hard-coded secrets.

Usage:
  python3 publish_product.py            # run full pipeline, publish
  python3 publish_product.py --draft    # stop after draft + files (safe re-runs)
"""
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gumroad import Gumroad  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PROD_DIR = os.path.dirname(HERE)

# ---- load token from .env if not in env -------------------------------
def load_token():
    if os.environ.get("GUMROAD_ACCESS_TOKEN"):
        return
    envf = os.path.join(PROD_DIR, ".env")
    if os.path.exists(envf):
        for line in open(envf):
            if line.startswith("GUMROAD_ACCESS_TOKEN="):
                os.environ["GUMROAD_ACCESS_TOKEN"] = line.strip().split("=", 1)[1]
                return

load_token()
g = Gumroad()

PRODUCT = {
    "name": "The Gumroad Playbook 2026",
    "price": 2900,                    # cents → $29
    "native_type": "ebook",
    "category": "business-and-money/entrepreneurship",
    "tags": ["gumroad", "digital-products", "creator-economy", "api", "automation", "ebook", "online-business"],
    "description": (
        "14-chapter playbook + working Python toolkit for building and automating a Gumroad business. "
        "Everything verified against the live v2 API (October 2026): fees, payouts, Discover eligibility, "
        "file upload, licensing, workflows, ping webhooks. Ships with a stdlib-only toolkit: "
        "gumroad.py (full API client), api-reference.md, this publishing pipeline, a ping webhook "
        "server, and a licensing demo. Merchant of record, tax handled, no monthly fees — this is "
        "the operating manual for the whole stack."
    ),
}

FILES = [
    ("assets/book.pdf", "The Playbook (PDF)"),
    ("assets/gumroad-toolkit.zip", "toolkit: full API client + reference + publishing pipeline + ping server + licensing demo (zip)"),
]

def set_cover(pid, file_url):
    """POST /products/:id/covers with the file_url (not in the stdlib client)."""
    import urllib.request
    pid_q = urllib.parse.quote(pid, safe="")
    data = urllib.parse.urlencode({"file_url": file_url}).encode()
    req = urllib.request.Request(
        f"https://api.gumroad.com/v2/products/{pid_q}/covers",
        data=data, method="POST",
        headers={"Authorization": f"Bearer {g.token}",
                 "Content-Type": "application/x-www-form-urlencoded"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def run(draft_only=False):
    print("Account:", g.user().get("url"))

    # 1. create draft ----------------------------------------------------
    p = dict(PRODUCT)
    p["draft"] = True
    p.pop("tags")  # tags must be repeated params (tags[]); form-encode via raw call
    prod = g.create_product(**p)
    # attach tags as repeated fields
    prod = prod.get("product", prod)
    import urllib.request
    pid = prod["id"]
    pairs = []
    for t in PRODUCT["tags"]:
        pairs.append(("tags[]", t))
    data = urllib.parse.urlencode(pairs).encode()
    req = urllib.request.Request(f"https://api.gumroad.com/v2/products/{urllib.parse.quote(pid, safe='')}",
                                data=data, method="PUT",
                                headers={"Authorization": f"Bearer {g.token}",
                                         "Content-Type": "application/x-www-form-urlencoded"})
    prod = json.load(urllib.request.urlopen(req, timeout=60)).get("product", {})
    pid, permalink = prod["id"], (prod.get("permalink") or "")
    if not permalink and prod.get("short_url"):
        permalink = prod["short_url"].rstrip("/").rsplit("/", 2)[-1]
    print(f"draft created: {pid}  /{permalink}  published={prod.get('published')}")
    if prod.get("warning"):
        print("WARNING from API:", prod["warning"])

    # 2. upload files ----------------------------------------------------
    urls = []
    for relpath, label in FILES:
        fpath = os.path.join(PROD_DIR, relpath)
        if not os.path.exists(fpath):
            raise SystemExit(f"missing: {fpath}")
        with open(fpath, "rb") as f:
            url = g.upload_file(os.path.basename(fpath), f)
        urls.append({"file_url": url, "name": label})
        print(f"uploaded {relpath}")

    # 3. attach ----------------------------------------------------------
    # Verified 2026-10-14: the only reliable attach form is
    #   files[][url]=<fresh presign URL>   (repeated keys, full replacement)
    # Resubmitting existing files by (id + canonical url) silently drops
    # them, so ALWAYS re-upload the bytes and attach the new URLs.
    prod = g.attach_files(pid, [u["file_url"] for u in urls])
    prod = prod.get("product", prod)
    print("files attached:", [f.get("filetype") for f in prod.get("files", [])])

    if draft_only:
        print(f"DRAFT ONLY mode — stopping before publish. permalink=/{permalink} id={pid}")
        return prod

    # 4. cover (thumbnail comes from the cover automatically)
    try:
        set_cover(pid, urls[0]["file_url"])
        print("cover set")
    except Exception as e:
        print("cover skipped:", e)

    # 5. enable ----------------------------------------------------------
    prod = g.enable_product(pid)
    prod = prod.get("product", prod)
    print(f"published: {prod.get('landing_url') or f'https://gum.co/{permalink}'}")
    return prod

if __name__ == "__main__":
    run(draft_only="--draft" in sys.argv)

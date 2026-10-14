#!/usr/bin/env python3
"""
Gumroad API v2 thin client — stdlib only (runs on Termux/any Python 3.8+).

Auth: a personal access token from https://gumroad.com/settings/advanced
      ("API applications" -> create app -> Generate access token) or an OAuth
      access_token. Send it either as `Authorization: Bearer <token>` or as the
      `access_token` form/query parameter (both work; every cURL in the official
      docs uses the parameter form).

Usage:
    from gumroad import Gumroad, GumroadError
    g = Gumroad(token="...")            # or GUMROAD_ACCESS_TOKEN env var
    products = g.list_all("products")   # auto-paginates
    g.create_product(name="Ebook", price=2000, native_type="ebook")
    with open("course.pdf","rb") as f:
        file_url = g.upload_file("course.pdf", f)
    g.create_product(name="Course", price=4900, files=[file_url])

Verified live against https://api.gumroad.com/v2 on 2026-10-14.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from email.utils import parsedate_to_datetime

API_BASE = "https://api.gumroad.com/v2"
PART_SIZE = 100 * 1024 * 1024  # 100 MB presigned parts
UPLOAD_TIMEOUT = 600


class GumroadError(Exception):
    """Raised when the API answers with success != true or a non-2xx status."""

    def __init__(self, message, status=None, body=None):
        super().__init__(message)
        self.status = status
        self.body = body



def _qid(product_id):
    import urllib.parse
    return urllib.parse.quote(product_id, safe='')
class Gumroad:

    def __init__(self, token=None, api_base=API_BASE):
        self.token = token or os.environ.get("GUMROAD_ACCESS_TOKEN")
        if not self.token:
            raise GumroadError(
                "No access token. Create one at https://gumroad.com/settings/advanced "
                "(API applications) or set GUMROAD_ACCESS_TOKEN."
            )
        self.api_base = api_base.rstrip("/")

    # ------------------------------------------------------------------ core
    def request(self, method, path, params=None, raw=False, timeout=60):
        """Do one API call. params is a dict; sent as form body (POST/PUT/DELETE)
        or query string (GET). Returns parsed JSON or raw bytes."""
        url = f"{self.api_base}{path}"
        data = None
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        p = {k: v for k, v in (params or {}).items() if v is not None}
        if method in ("GET",):
            if p:
                url += ("&" if "?" in url else "?") + urllib.parse.urlencode(p, doseq=True)
        else:
            data = urllib.parse.urlencode(p, doseq=True).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
                if raw or not body:
                    return body
                return json.loads(body)
        except urllib.error.HTTPError as e:
            body = e.read()
            if raw:
                raise GumroadError(f"HTTP {e.code}", e.code, body)
            try:
                d = json.loads(body)
            except Exception:
                d = None
            # 401 on gumroad has an EMPTY body; surface a helpful message anyway.
            msg = (d or {}).get("message") if isinstance(d, dict) else None
            if not msg:
                msg = f"HTTP {e.code}"
                if e.code == 401:
                    msg += " — bad/missing access token"
                elif body:
                    msg += " — " + body[:200].decode("utf-8", "replace")
            raise GumroadError(msg, e.code, d)
        except urllib.error.URLError as e:
            raise GumroadError(f"network error: {e.reason}")

    # ------------------------------------------------------- pagination util
    def list_all(self, resource, params=None, key=None, page_key_param="page_key"):
        """Follow `next_page_key` until exhausted. `key` is the plural response
        field (defaults to the resource name, e.g. products/sales/subscribers)."""
        key = key or resource
        out, p = [], dict(params or {})
        while True:
            r = self.request("GET", f"/{resource}", p)
            out.extend(r.get(key, []))
            nk = r.get("next_page_key")
            if not nk:
                return out
            p[page_key_param] = nk

    # ------------------------------------------------------------------ user
    def user(self):
        return self.request("GET", "/user").get("user", {})

    def refund_policy(self):
        return self.request("GET", "/refund_policy")

    def set_refund_policy(self, period, fine_print=None):
        """period: "inherit"|"none"|"7"|"14"|"30"|"183"."""
        return self.request("PUT", "/refund_policy",
                            {"refund_policy_period": period, "refund_fine_print": fine_print})

    def custom_html(self):
        return self.request("GET", "/user/custom_html")

    def set_custom_html(self, html):
        return self.request("PUT", "/user/custom_html", {"custom_html": html})

    # --------------------------------------------------------------- products
    def products(self, paginated=False):
        return self.request("GET", "/products", {"paginated": "true" if paginated else "false"})

    def product(self, product_id):
        return self.request("GET", f"/products/{product_id}").get("product", {})

    def create_product(self, name, price, **params):
        """POST /v2/products. Extra params: native_type ("digital"|"course"|"ebook"|
        "membership"|"bundle"|"coffee"|"call"|"commission", default digital, immutable),
        description (HTML), draft, published, custom_permalink, price_currency_type,
        subscription_duration, customizable_price, suggested_price_cents,
        max_purchase_count, category|taxonomy_id, tags[], custom_summary,
        refund_period, refund_fine_print, rich_content[], files[file_url]."""
        params.update({"name": name, "price": price})
        return self.request("POST", "/products", params)

    def update_product(self, product_id, **params):
        return self.request("PUT", f"/products/{product_id}", params)

    def delete_product(self, product_id):
        return self.request("DELETE", f"/products/{product_id}")

    def enable_product(self, product_id):
        return self.request("PUT", f"/products/{product_id}/enable")

    def disable_product(self, product_id):
        return self.request("PUT", f"/products/{product_id}/disable")

    def categories(self):
        return self.request("GET", "/categories").get("categories", [])

    def reviews(self, product_id, page_key=None):
        return self.request("GET", f"/products/{product_id}/reviews",
                            {"page_key": page_key})

    # ------------------------------------------------------- files & uploads
    def presign(self, filename, file_size):
        """Step 1 of 4: start a multipart upload. Returns upload_id/key/file_url/parts."""
        return self.request("POST", "/files/presign",
                            {"filename": filename, "file_size": file_size})

    def complete_upload(self, upload_id, key, parts):
        """Step 3: parts = [{"part_number": 1, "etag": "..."}, ...].
        API wants bracketed keys: parts[0][part_number], parts[0][etag]."""
        pairs = []
        for p in parts:
            pairs.append(("parts[][part_number]", p["part_number"]))
            pairs.append(("parts[][etag]", p["etag"]))
        import urllib.parse as _up
        body = _up.urlencode([("upload_id", upload_id), ("key", key)] + pairs)
        hdrs = {"Authorization": "Bearer " + self.token} if self.token else {}
        req = urllib.request.Request(self.api_base + "/files/complete",
                                     data=body.encode(), method="POST", headers=hdrs)
        with urllib.request.urlopen(req, timeout=UPLOAD_TIMEOUT) as r:
            return json.loads(r.read() or b"{}")
        return self.request("POST", "/files/complete", params)

    def set_cover(self, product_id, url):
        """POST /products/:id/covers. url MUST be a publicly reachable image
        URL (JPEG/PNG/GIF) or a YouTube/Vimeo URL — Gumroad fetches it
        server-side and stores a copy. A pre-signed S3 attachment URL (the
        one /files/presign returns) is NOT fetchable (403) — host the image
        somewhere public first (e.g. raw.githubusercontent.com, your CDN)."""
        return self.request("POST", f"/products/{_qid(product_id)}/covers",
                            {"url": url})

    def delete_cover(self, product_id, cover_id):
        return self.request("DELETE", f"/products/{_qid(product_id)}/covers/{cover_id}")

    def set_thumbnail(self, product_id, url):
        """POST /products/:id/thumbnail. MUST be a square image URL —
        a non-square PNG 400s with 'Please upload a square thumbnail.'."""
        return self.request("POST", f"/products/{_qid(product_id)}/thumbnail",
                            {"url": url})

    def delete_thumbnail(self, product_id):
        return self.request("DELETE", f"/products/{_qid(product_id)}/thumbnail")

    def add_media(self, url=None, signed_blob_id=None, name=None):
        """POST /media. Uploads an image (<=10 MB) to the media library.
        Requires the edit_profile scope (an account-only token is rejected
        with 401). signed_blob_id comes from a /direct_uploads reservation."""
        params = {"name": name}
        if url:
            params["url"] = url
        elif signed_blob_id:
            params["signed_blob_id"] = signed_blob_id
        else:
            raise ValueError("need url or signed_blob_id")
        return self.request("POST", "/media", params)

    def delete_media(self, media_id):
        return self.request("DELETE", f"/media/{media_id}")

    def abort_upload(self, upload_id, key):
        """Cancel a failed multipart upload. status is 'accepted' (retry until
        'already_gone') or 'already_gone'."""
        return self.request("POST", "/files/abort",
                            {"upload_id": upload_id, "key": key})

    def _put_part(self, presigned_url, chunk):
        req = urllib.request.Request(presigned_url, data=chunk, method="PUT")
        with urllib.request.urlopen(req, timeout=UPLOAD_TIMEOUT) as r:
            return r.headers["ETag"]

    def upload_file(self, filename, fileobj, chunk_size=PART_SIZE, on_progress=None):
        """All 4 steps in one call. fileobj is an open binary file. Returns the
        file_url to pass as files[file_url] on create/update product. Max 20 GB."""
        size = fileobj.seek(0, 2)
        fileobj.seek(0)
        if size > 20 * 1024**3:
            raise GumroadError("file exceeds the 20 GB limit")
        ps = self.presign(filename, size)
        parts, n = [], 1
        while True:
            chunk = fileobj.read(chunk_size)
            if not chunk:
                break
            etag = self._put_part(next(p["presigned_url"] for p in ps["parts"]
                                      if p["part_number"] == n), chunk)
            parts.append({"part_number": n, "etag": etag})
            if on_progress:
                on_progress(n, len(parts), size)
            n += 1
        self.complete_upload(ps["upload_id"], ps["key"], parts)
        return ps["file_url"]

    def attach_files(self, product_id, file_urls, client_id=None):
        """Attach files to a product (PUT /v2/products/:id).

        Verified against the live API 2026-10-14:
        - The ONLY working form is repeated files[][url]=<fresh presign URL>.
        - This is a FULL REPLACEMENT: any file you omit is deleted.
        - Resubmitting files[][id]=<file_id> + its canonical URL does NOT
          work — the server drops the entry silently (returns files: []).
          Re-uploading the bytes via /files/presign and passing the new URL
          is the reliable path; do that for every file on every attach.
        - New files may include files[][external_id]=cli-upload-1; the
          response then carries file_id_mappings (client id -> canonical
          ProductFile id)."""
        pairs = []
        for u in file_urls:
            pairs.append(("files[][url]", u))
        if client_id:
            pairs.append(("files[][external_id]", client_id))
        import urllib.parse as _up
        body = _up.urlencode(pairs)
        pid_q = urllib.parse.quote(product_id, safe="")
        req = urllib.request.Request(
            f"{self.api_base}/products/{pid_q}", data=body.encode(), method="PUT",
            headers={"Content-Type": "application/x-www-form-urlencoded",
                     "Authorization": f"Bearer {self.token}"})
        with urllib.request.urlopen(req, timeout=UPLOAD_TIMEOUT) as r:
            return json.loads(r.read() or b"{}")

    # ------------------------------------------------------------- offer codes
    def offer_codes(self, product_id):
        return self.request("GET", f"/products/{product_id}/offer_codes").get("offer_codes", [])

    def create_offer_code(self, product_id, name, amount_off=None, offer_type="cents",
                          max_purchase_count=None, minimum_amount_cents=None, universal=False):
        """offer_type "cents" (amount_off in cents) or "percent" (amount_off = 0-100)."""
        return self.request("POST", f"/products/{product_id}/offer_codes",
                            {"name": name, "amount_off": amount_off, "offer_type": offer_type,
                             "max_purchase_count": max_purchase_count,
                             "minimum_amount_cents": minimum_amount_cents,
                             "universal": "true" if universal else "false"})

    def update_offer_code(self, product_id, offer_code_id, **params):
        return self.request("PUT", f"/products/{product_id}/offer_codes/{offer_code_id}", params)

    def delete_offer_code(self, product_id, offer_code_id):
        return self.request("DELETE", f"/products/{product_id}/offer_codes/{offer_code_id}")

    # ---------------------------------------------------------- custom fields
    def custom_fields(self, product_id):
        return self.request("GET", f"/products/{product_id}/custom_fields").get("custom_fields", [])

    def create_custom_field(self, product_id, name, required=False):
        return self.request("POST", f"/products/{product_id}/custom_fields",
                            {"name": name, "required": "true" if required else "false"})

    def update_custom_field(self, product_id, name, required=False):
        from urllib.parse import quote
        return self.request("PUT", f"/products/{product_id}/custom_fields/{quote(name)}",
                            {"required": "true" if required else "false"})

    def delete_custom_field(self, product_id, name):
        from urllib.parse import quote
        return self.request("DELETE", f"/products/{product_id}/custom_fields/{quote(name)}")

    # ------------------------------------------------- variant categories/var's
    def variant_categories(self, product_id):
        return self.request("GET", f"/products/{product_id}/variant_categories") \
                   .get("variant_categories", [])

    def create_variant_category(self, product_id, title):
        return self.request("POST", f"/products/{product_id}/variant_categories",
                            {"title": title})

    def create_variant(self, product_id, variant_category_id, name, price_difference=None):
        return self.request("POST",
                            f"/products/{product_id}/variant_categories/"
                            f"{variant_category_id}/variants",
                            {"name": name, "price_difference": price_difference})

    # ------------------------------------------------------------------ sales
    def sales(self, after=None, before=None, product_id=None, email=None,
              order_id=None, name=None, license_key=None, page_key=None):
        return self.request("GET", "/sales",
                            {"after": after, "before": before, "product_id": product_id,
                             "email": email, "order_id": order_id, "name": name,
                             "license_key": license_key, "page_key": page_key})

    def all_sales(self, **filters):
        return self.list_all("sales", filters)

    def sale(self, sale_id):
        return self.request("GET", f"/sales/{sale_id}").get("sale", {})

    def refund_sale(self, sale_id, amount=None):
        """Partial refund if amount (cents) given, full refund otherwise."""
        return self.request("PUT", f"/sales/{sale_id}/refund", {"amount": amount})

    def mark_as_shipped(self, sale_id, tracking_number=None):
        return self.request("PUT", f"/sales/{sale_id}/mark_as_shipped",
                            {"tracking_number": tracking_number})

    def resend_receipt(self, sale_id):
        return self.request("POST", f"/sales/{sale_id}/resend_receipt")

    def revoke_access(self, sale_id):
        return self.request("PUT", f"/sales/{sale_id}/revoke_access")

    def undo_revoke_access(self, sale_id):
        return self.request("PUT", f"/sales/{sale_id}/undo_revoke_access")

    # ------------------------------------------------------------- subscribers
    def subscribers(self, product_id, email=None, paginated=False, page_key=None):
        return self.request("GET", f"/products/{product_id}/subscribers",
                            {"email": email,
                             "paginated": "true" if paginated else "false",
                             "page_key": page_key})

    def all_subscribers(self, product_id, **filters):
        return self.list_all(f"products/{product_id}/subscribers", filters,
                             key="subscribers")

    def subscriber(self, subscriber_id):
        return self.request("GET", f"/subscribers/{subscriber_id}").get("subscriber", {})

    # --------------------------------------------------------------- licenses
    def verify_license(self, product_id, license_key, increment_uses_count=True):
        """Does NOT require an OAuth/access token; perfect for in-app licensing."""
        return self.request("POST", "/licenses/verify",
                            {"product_id": product_id, "license_key": license_key,
                             "increment_uses_count": "true" if increment_uses_count else "false"})

    def _lic(self, action, product_id, license_key):
        return self.request("PUT", f"/licenses/{action}",
                            {"product_id": product_id, "license_key": license_key})

    def enable_license(self, product_id, license_key):
        return self._lic("enable", product_id, license_key)

    def disable_license(self, product_id, license_key):
        return self._lic("disable", product_id, license_key)

    def decrement_license_uses(self, product_id, license_key):
        return self._lic("decrement_uses_count", product_id, license_key)

    def rotate_license(self, product_id, license_key):
        return self._lic("rotate", product_id, license_key)

    # ---------------------------------------------------------------- payouts
    def payouts(self):
        return self.request("GET", "/payouts").get("payouts", [])

    def payout(self, payout_id):
        return self.request("GET", f"/payouts/{payout_id}").get("payout", {})

    def upcoming_payout(self):
        return self.request("GET", "/payouts/upcoming")

    # ------------------------------------------------------------- tax/earnings
    def tax_forms(self, year=None):
        return self.request("GET", "/tax_forms", {"year": year}).get("tax_forms", [])

    def download_tax_form(self, year, tax_form_type, dest_path):
        """tax_form_type: "us_1099_k" or "us_1099_misc". Writes the PDF to dest_path."""
        raw = self.request("GET", f"/tax_forms/{year}/{tax_form_type}/download", raw=True)
        with open(dest_path, "wb") as f:
            f.write(raw)
        return dest_path

    def earnings(self, year):
        return self.request("GET", "/earnings", {"year": year})

    # ----------------------------------------------------------------- emails
    def emails(self, type=None, page_key=None):
        return self.request("GET", "/emails", {"type": type, "page_key": page_key})

    def create_email(self, subject, body, audience="all", publish=False):
        """audience: "all"|"audience"|"customers"|"seller"|"followers".
        publish=True sends immediately; otherwise saved as draft."""
        return self.request("POST", "/emails",
                            {"subject": subject, "body": body, "audience": audience,
                             "publish": "true" if publish else "false"})

    def preview_email(self, email_id):
        return self.request("POST", f"/emails/{email_id}/preview")

    def send_email(self, email_id):
        return self.request("POST", f"/emails/{email_id}/send")

    def schedule_email(self, email_id, send_at):
        """send_at: ISO-8601 timestamp (UTC), e.g. 2026-12-01T09:00:00Z."""
        return self.request("POST", f"/emails/{email_id}/schedule", {"send_at": send_at})

    def unschedule_email(self, email_id):
        return self.request("POST", f"/emails/{email_id}/unschedule")

    def delete_email(self, email_id):
        return self.request("DELETE", f"/emails/{email_id}")

    # -------------------------------------------------------------- workflows
    def workflows(self):
        return self.request("GET", "/workflows").get("workflows", [])

    def workflow(self, workflow_id):
        return self.request("GET", f"/workflows/{workflow_id}").get("workflow", {})

    def add_workflow_email(self, workflow_id, subject, message, delay_amount=0,
                           delay_unit="day"):
        return self.request("POST", f"/workflows/{workflow_id}/emails",
                            {"subject": subject, "message": message,
                             "delay_amount": delay_amount, "delay_unit": delay_unit})

    # --------------------------------------------- resource subscriptions (webhooks)
    def subscribe(self, resource_name, post_url):
        """resource_name: sale|refund|dispute|dispute_won|cancellation|
        subscription_updated|subscription_ended|subscription_restarted."""
        return self.request("PUT", "/resource_subscriptions",
                            {"resource_name": resource_name, "post_url": post_url})

    def subscriptions(self):
        return self.request("GET", "/resource_subscriptions").get("resource_subscriptions", [])

    def unsubscribe(self, resource_subscription_id):
        return self.request("DELETE", f"/resource_subscriptions/{resource_subscription_id}")


# --------------------------------------------------------------------- Ping
# Gumroad "Ping" webhooks are UNSIGNED HTTP POSTs — there is no HMAC to verify.
# Treat a Ping payload as untrusted input; authenticate anything you act on by
# re-fetching the sale/license with the API (e.g. verify_license / sale(id)).
PING_FIELDS = [
    "sale_id", "sale_timestamp", "order_number", "seller_id", "product_id",
    "product_permalink", "short_product_id", "product_name", "email", "url_params",
    "full_name", "purchaser_id", "subscription_id", "ip_country", "price",
    "recurrence", "variants", "offer_code", "test", "custom_fields",
    "shipping_information", "is_recurring_charge", "is_preorder_authorization",
    "license_key", "quantity", "shipping_rate", "affiliate",
    "affiliate_credit_amount_cents", "is_gift_receiver_purchase", "gifter_email",
    "gift_price", "refunded", "discover_fee_charged", "can_contact", "referrer",
    "gumroad_fee", "card", "resource_name", "retry_count",
]


def parse_ping(form):
    """Decode a Ping POST (form-urlencoded). variants/custom_fields/url_params
    arrive as JSON strings; price fields are USD cents."""
    out = {}
    for k, v in form.items():
        if k in ("variants", "custom_fields", "url_params") and isinstance(v, str):
            try:
                v = json.loads(v)
            except Exception:
                pass
        out[k] = v
    return out


if __name__ == "__main__":
    import sys
    g = Gumroad()  # GUMROAD_ACCESS_TOKEN
    cmd = sys.argv[1] if len(sys.argv) > 1 else "user"
    if cmd == "user":
        print(json.dumps(g.user(), indent=2))
    elif cmd == "products":
        print(json.dumps(g.list_all("products"), indent=2))
    elif cmd == "sales":
        print(json.dumps(g.sales(), indent=2))
    elif cmd == "categories":
        print(json.dumps(g.categories(), indent=2))
    else:
        print("usage: gumroad.py [user|products|sales|categories]")

#!/usr/bin/env python3
"""Fulfillment webhook server (the pattern from Chapter 8: verify-before-fulfill).

Gumroad "Ping" posts are UNSIGNED — there is no HMAC. This server never
trusts the payload: it re-fetches the sale from the API before doing anything.

Stdlib only (http.server). Runs anywhere Python 3.8+ runs.

  GUMROAD_ACCESS_TOKEN=... python3 ping_server.py 8080

Gumroad posts to:  /ping
Events handled: sale, refund (extend access / revoke on refund).

In production you need a public URL (tunnel/relay). Gumroad retries Ping
posts a few times; a 2xx response stops the retries.
"""
import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gumroad import Gumroad, parse_ping  # noqa: E402

g = None  # created in main() after token resolution


def get_g():
    global g
    if g is None:
        if not os.environ.get("GUMROAD_ACCESS_TOKEN"):
            envf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
            if os.path.exists(envf):
                for line in open(envf):
                    if line.startswith("GUMROAD_ACCESS_TOKEN="):
                        os.environ["GUMROAD_ACCESS_TOKEN"] = line.strip().split("=", 1)[1]
        g = Gumroad()
    return g


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("[ping] " + fmt % args + "\n")

    def _json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # health endpoint
        self._json({"ok": True})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8", "replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            # Ping can also be form-encoded
            payload = {k: v[0] for k, v in
                      urllib.parse.parse_qs(raw, keep_blank_values=True).items()}
        ping = parse_ping(payload)
        kind = ping.get("resource_name", "sale")
        gi = get_g()

        # ---- VERIFY-BEFORE-FULFILL: the payload is untrusted -------------
        sale_id = ping.get("sale_id")
        if kind == "sale" and not ping.get("test"):
            try:
                sale = gi.sale(sale_id)
            except Exception as e:
                print(f"could not re-verify sale {sale_id}: {e}")
                self._json({"ok": False, "reason": "unverifiable_sale"}, 402)
                return
            # now it's real — do fulfillment (email license, push to app, etc.)
            print(f"REAL SALE #{ping.get('order_number')}: "
                  f"{ping.get('product_name')} -> {ping.get('email')}")
            # Example: grant a license key
            key = ping.get("license_key")
            if key:
                print(f"license granted: {key}")
            # TODO: your fulfillment here (S3 presign, LMS enrollment, ...)

        elif kind == "refund":
            print(f"REFUND for sale {sale_id}; revoke access if needed:")
            # try: gi.revoke_access(sale_id)
            pass

        self._json({"ok": True})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    get_g()
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"ping server on :{port} — point a Gumroad Ping / resource subscription at /ping")
    srv.serve_forever()


if __name__ == "__main__":
    main()

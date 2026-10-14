#!/usr/bin/env python3
"""Sales monitor — no external dependencies.

Polls GET /sales (view_sales scope) and prints anything new since the last
checkpoint. The checkpoint is stored in .sales_seen.json next to this file,
so two runs never double-report.

Run it on a cron (e.g. every 15 min) or just run it by hand:
  python3 sales_monitor.py
  python3 sales_monitor.py --since 2026-10-14      # force a window
  python3 sales_monitor.py --verbose                # show all fields

Why polling instead of Ping? Ping posts are unsigned and you need a public
URL to receive them (tunnel/relay). Polling GET /sales needs no public
endpoint and no secrets beyond the token — the honest, low-ops choice for
a single product. Switch to Ping + verify-before-fulfill (ping_server.py)
when volume justifies it.

Fees reminder: direct sale = 10% + $0.50; Discover sale to a NEW customer =
30%. Use the formatted fields, not the raw cents, when you report revenue.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, ".sales_seen.json")
API = "https://api.gumroad.com/v2/sales"


def load_token():
    if os.environ.get("GUMROAD_ACCESS_TOKEN"):
        return
    envf = os.path.join(os.path.dirname(HERE), ".env")
    if os.path.exists(envf):
        for line in open(envf):
            if line.startswith("GUMROAD_ACCESS_TOKEN="):
                os.environ["GUMROAD_ACCESS_TOKEN"] = line.strip().split("=", 1)[1]


def get(url, params, token):
    q = urllib.parse.urlencode(params)
    full = url + "?" + q if params else url
    req = urllib.request.Request(full, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def main():
    load_token()
    token = os.environ.get("GUMROAD_ACCESS_TOKEN")
    if not token:
        sys.exit("no token")

    since = None
    if "--since" in sys.argv:
        since = sys.argv[sys.argv.index("--since") + 1]
    verbose = "--verbose" in sys.argv

    state = {}
    if os.path.exists(STATE):
        state = json.load(open(STATE))

    params = {"paginated": "true"}
    if since:
        params["after"] = since

    seen = set(state.get("seen", []))
    new = []
    while True:
        r = get(API, params, token)
        for s in r.get("sales", []):
            sid = s.get("id")
            if sid in seen:
                continue
            new.append(s)
            seen.add(sid)
        params["page_key"] = r.get("next_page_key")
        if not r.get("next_page_key"):
            break

    if new:
        for s in new:
            if verbose:
                print(json.dumps(s, indent=2))
            else:
                print(f"SALE {s.get('order_number')} | {s.get('product', {}).get('name')} "
                      f"${(s.get('price_cents', 0) / 100):.2f} | {s.get('email', '?')}")
        state["seen"] = list(seen)
        json.dump(state, open(STATE, "w"))
    else:
        print("no new sales")

    # keep the state file small
    if len(seen) > 5000:
        state["seen"] = list(seen)[-5000:]
        json.dump(state, open(STATE, "w"))


if __name__ == "__main__":
    main()

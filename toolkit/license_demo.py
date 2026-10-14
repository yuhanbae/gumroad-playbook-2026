#!/usr/bin/env python3
"""Licensing flow demo (Chapter 9).

`POST /v2/licenses/verify` needs NO OAuth application — it's the primitive
for apps that ship with license keys. This demo shows the full lifecycle:

  verify  -> enable -> disable -> decrement -> rotate

Run:  GUMROAD_ACCESS_TOKEN=... python3 license_demo.py <product_id> <license_key>
      (any product id + key works for shape; verify returns 404 JSON for a
       bad key instead of crashing — see Gotchas in the skill)
"""
import sys

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from gumroad import Gumroad, GumroadError  # noqa: E402

g = Gumroad()


def main():
    import os
    product_id = sys.argv[1]
    key = sys.argv[2]
    if not os.environ.get("GUMROAD_ACCESS_TOKEN"):
        envf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
        if os.path.exists(envf):
            for line in open(envf):
                if line.startswith("GUMROAD_ACCESS_TOKEN="):
                    os.environ["GUMROAD_ACCESS_TOKEN"] = line.strip().split("=", 1)[1]
    g = Gumroad()

    # 1. verify — gate on this before enabling any feature
    try:
        lic = g.verify_license(product_id, key, increment_uses_count=False)
        print("LICENSE VALID:")
        print(f"  id:    {lic.get('id')}")
        print(f"  uses:  {lic.get('uses')} / unlimited? 'uses' absent = no limit")
        print(f"  user:  {lic.get('user_email')}")
        print(f"  status: {lic.get('status')}")
    except GumroadError as e:
        print(f"license INVALID (status {e.status}): {e.body}")
        return

    # 2. support flows (admin-side, need your token)
    print("\nadmin flows:")
    try:
        g.disable_license(product_id, key)
        print("  disabled (customer's refund/expiry)")
        g.enable_license(product_id, key)
        print("  re-enabled")
        g.decrement_license_uses(product_id, key)
        print("  decremented one use")
        g.rotate_license(product_id, key)
        print("  rotated (new key issued — tell the customer the old one is dead)")
    except GumroadError as e:
        print(f"  admin flow stopped: {e.status} {e.body}")

    print("\nrule: verify with increment_uses_count=False on app start (cheap, "
          "no side effects); only call with increment_uses_count=True when a "
          "seat is genuinely consumed (install), and decrement on uninstall.")


if __name__ == "__main__":
    main()

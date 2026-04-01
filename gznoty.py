#!/usr/bin/env python3
"""Scrape Game Nerdz Deal of the Day and notify via ntfy."""

import argparse
import base64
import json
import re
import sys
import requests

URL = "https://www.gamenerdz.com/deal-of-the-day"
STOREPASS_API = "https://store.storepass.co"
STORE_ID = "OvpVz0pNlL"
NTFY_TOPIC = "yrvn-gz"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def scrape_deal():
    resp = requests.get(URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    # Product data is in a base64-encoded bodl JSON blob
    m = re.search(r'window\.bodl\s*=\s*JSON\.parse\(decodeBase64\("([^"]+)"\)', resp.text)
    if not m:
        with open("debug.html", "w") as f:
            f.write(resp.text)
        print("FAIL:no bodl data found, saved debug.html")
        sys.exit(1)

    data = json.loads(base64.b64decode(m.group(1)))
    items = data["events"][0]["bodl_v1_product_category_viewed"]["line_items"]
    if not items:
        print("FAIL:no items in deal")
        sys.exit(1)

    item = items[0]
    title = item["product_name"]
    sale_price = item["sale_price"]
    retail_price = item["retail_price"]
    discount = item["discount"]

    # Try to get stock from StorePass API
    stock = get_stock(item["product_id"])

    return {
        "title": title,
        "price": f"${sale_price:.2f} (was ${retail_price:.2f}, save ${discount:.2f})",
        "stock": stock,
    }


def get_stock(product_id):
    try:
        resp = requests.get(
            f"{STOREPASS_API}/saas/category/223/products",
            params={"store_id": STORE_ID},
            headers=HEADERS,
            timeout=10,
        )
        if resp.ok:
            products = resp.json()
            for p in products if isinstance(products, list) else []:
                pid = str(p.get("product_id", p.get("id", "")))
                if pid == str(product_id):
                    qty = p.get("stock", p.get("inventory_quantity", p.get("quantity")))
                    if qty is not None:
                        return f"{qty} left"
    except Exception:
        pass
    return "N/A"


def notify(deal):
    body = f"{deal['title']}\nPrice: {deal['price']}\nStock: {deal['stock']}"
    resp = requests.post(
        NTFY_URL,
        data=body.encode(),
        headers={
            "Title": "GN Deal of the Day",
            "Tags": "game_die,moneybag",
        },
        timeout=10,
    )
    resp.raise_for_status()
    print(f"OK:{body}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    deal = scrape_deal()

    if args.test:
        print(f"{deal['title']}|{deal['price']}|{deal['stock']}")
        return

    notify(deal)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Scrape Game Nerdz Deal of the Day and notify via ntfy."""

import argparse
import base64
import json
import re
import sys
import requests

URL = "https://www.gamenerdz.com/deal-of-the-day"
STORE_ID = "OvpVz0pNlL"
CATEGORY_ID = 223
NTFY_TOPIC = "yrvn-gz"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# StorePass API endpoints to try for stock data
STOREPASS_URLS = [
    f"https://store.storepass.co/saas/products?store_id={STORE_ID}&category_id={CATEGORY_ID}",
    f"https://store.storepass.co/saas/category/{CATEGORY_ID}?store_id={STORE_ID}",
    f"https://store.storepass.co/saas/products/{STORE_ID}?category_id={CATEGORY_ID}",
    f"https://store.storepass.co/saas/{STORE_ID}/products?category_id={CATEGORY_ID}",
    f"https://store.storepass.co/saas/store/{STORE_ID}/category/{CATEGORY_ID}",
]


def scrape_deal():
    resp = requests.get(URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    m = re.search(r'window\.bodl\s*=\s*JSON\.parse\(decodeBase64\("([^"]+)"\)', resp.text)
    if not m:
        with open("debug.html", "w") as f:
            f.write(resp.text)
        print("FAIL:no bodl data, saved debug.html")
        sys.exit(1)

    data = json.loads(base64.b64decode(m.group(1)))
    items = data["events"][0]["bodl_v1_product_category_viewed"]["line_items"]
    if not items:
        print("FAIL:no items in deal")
        sys.exit(1)

    item = items[0]
    stock = get_stock(item["product_name"], item["product_id"])

    return {
        "title": item["product_name"],
        "price": f"${item['sale_price']:.2f} (was ${item['retail_price']:.2f}, save ${item['discount']:.2f})",
        "stock": stock,
    }


def get_stock(product_name, product_id):
    results = []
    # Try 1: StorePass search by name with all required params
    queries = [
        {"store_id": STORE_ID, "name": product_name, "mongo": "true",
         "limit": "1", "sort": "Relevance", "override_buylist_gt_price": "true",
         "product_line": "All",
         "fields": "id,productId,stock,availability,name,inventoryLevels"},
        {"store_id": STORE_ID, "mongo": "true", "limit": "30",
         "override_buylist_gt_price": "true", "product_line": "All",
         "fields": "id,productId,stock,availability,name,inventoryLevels"},
    ]
    for params in queries:
        try:
            resp = requests.get(
                "https://store.storepass.co/saas/search",
                params=params, headers=HEADERS, timeout=10,
            )
            results.append(f"url:{resp.url}\nstatus:{resp.status_code}\n{resp.text[:1500]}\n")
            if resp.ok:
                data = resp.json()
                products = data.get("products", [])
                for p in products:
                    if str(p.get("productId", "")) == str(product_id) or p.get("name", "") == product_name:
                        stock = p.get("stock")
                        if stock is not None:
                            return f"{stock} left"
        except Exception as e:
            results.append(f"exception:{e}\n")
    with open("debug_stock.txt", "w") as f:
        f.write("\n===\n".join(results))
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

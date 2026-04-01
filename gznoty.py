#!/usr/bin/env python3
"""Scrape Game Nerdz Deal of the Day and notify via ntfy."""

import argparse
import sys
import requests
from playwright.sync_api import sync_playwright

URL = "https://www.gamenerdz.com/deal-of-the-day"
NTFY_TOPIC = "yrvn-gz"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"


def scrape_deal():
    api_responses = []

    def capture_response(response):
        if "storepass.co/saas/search" in response.url:
            try:
                api_responses.append(response.json())
            except Exception:
                pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("response", capture_response)
        page.goto(URL, wait_until="networkidle", timeout=30000)
        browser.close()

    if not api_responses:
        print("FAIL:no storepass API calls captured")
        sys.exit(1)

    # Find the response with products
    for data in api_responses:
        products = data.get("products", [])
        if products:
            p = products[0]
            return {
                "title": p.get("name", "N/A"),
                "price": f"${p['salePrice']}" if p.get("salePrice") else p.get("price", "N/A"),
                "stock": f"{p['stock']} left" if p.get("stock") is not None else "N/A",
            }

    print("FAIL:API responded but no products")
    sys.exit(1)


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

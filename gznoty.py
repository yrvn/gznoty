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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle", timeout=30000)
        page.wait_for_selector(".store-pass-product-name", timeout=15000)

        title = page.text_content(".store-pass-product-name")
        price = page.text_content(".store-pass-product-price")
        msrp = page.text_content(".store-pass-product-msrp")
        stock = page.text_content(".store-pass-product-stock-row")

        browser.close()

    title = title.strip() if title else "N/A"
    price = price.strip() if price else "N/A"
    msrp = msrp.strip() if msrp else ""
    stock = stock.strip() if stock else "N/A"

    price_str = f"{price} (was {msrp})" if msrp else price

    return {"title": title, "price": price_str, "stock": stock}


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

    notify(deal)


if __name__ == "__main__":
    main()

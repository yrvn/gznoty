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
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector(".product-imports .card", timeout=15000)

        deal = page.evaluate("""() => {
            const card = document.querySelector('.product-imports .card');
            if (!card) return null;
            const title = card.querySelector('.card-title a') || card.querySelector('a');
            const price = card.querySelector('[class*=price]');
            const stock = card.querySelector('[class*=stock]')
                || card.querySelector('[class*=quantity]')
                || card.querySelector('[class*=inventory]');
            return {
                title: title ? title.innerText.trim() : null,
                price: price ? price.innerText.trim() : null,
                stock: stock ? stock.innerText.trim() : null,
            };
        }""")

        if not deal or not deal.get("title"):
            debug = page.evaluate("""() => {
                const el = document.querySelector('.product-imports');
                return el ? el.innerText.substring(0, 500) : 'no .product-imports';
            }""")
            browser.close()
            print(f"FAIL:{debug}")
            sys.exit(1)

        browser.close()

    return {
        "title": deal["title"],
        "price": deal.get("price") or "N/A",
        "stock": deal.get("stock") or "N/A",
    }


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

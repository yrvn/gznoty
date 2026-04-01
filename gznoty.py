#!/usr/bin/env python3
"""Scrape Game Nerdz Deal of the Day and notify via ntfy."""

import argparse
import sys
import re
import requests
from requests_html import HTMLSession

URL = "https://www.gamenerdz.com/deal-of-the-day"
NTFY_TOPIC = "yrvn-gz"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"


def scrape_deal():
    session = HTMLSession()
    resp = session.get(URL)
    resp.html.render(timeout=30, sleep=3)

    # Find the product card in the rendered page
    card = resp.html.find(".product-imports .card", first=True)
    if not card:
        text = resp.html.find(".product-imports", first=True)
        debug = text.text[:500] if text else resp.html.text[:500]
        print(f"FAIL:no card found|{debug}")
        sys.exit(1)

    title_el = card.find(".card-title a", first=True) or card.find("a", first=True)
    price_el = (
        card.find(".storepass-price-value", first=True)
        or card.find("[class*=price]", first=True)
    )
    stock_el = (
        card.find("[class*=stock]", first=True)
        or card.find("[class*=quantity]", first=True)
        or card.find("[class*=inventory]", first=True)
    )

    title = title_el.text.strip() if title_el else None
    if not title:
        print(f"FAIL:no title|{card.text[:500]}")
        sys.exit(1)

    price = price_el.text.strip() if price_el else "N/A"
    stock = stock_el.text.strip() if stock_el else "N/A"

    return {"title": title, "price": price, "stock": stock}


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

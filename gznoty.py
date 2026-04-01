#!/usr/bin/env python3
"""Scrape Game Nerdz Deal of the Day and notify via ntfy."""

import argparse
import sys
import requests
from bs4 import BeautifulSoup

URL = "https://www.gamenerdz.com/deal-of-the-day"
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
    soup = BeautifulSoup(resp.text, "html.parser")

    product = soup.select_one(".dotd-product, .dealoftheday-product, [data-product-title]")

    if product:
        title_el = (
            product.select_one(".card-title a, .product-title a, h4 a, h3 a")
            or product.select_one("a[href*='/deal-of-the-day']")
            or product.select_one("a")
        )
        price_el = product.select_one(
            ".price--withoutTax, .price--main, .sale-price, .price span"
        )
        stock_el = product.select_one(
            ".dotd-stock, .stock-level, [data-stock], .inventory, .product-stock"
        )
    else:
        title_el = (
            soup.select_one("[data-product-title]")
            or soup.select_one("h1.productView-title")
            or soup.select_one(".productView-title")
            or soup.select_one(".page-content h1")
            or soup.select_one(".card-title a")
        )
        price_el = (
            soup.select_one(".price--withoutTax")
            or soup.select_one(".productView-price .price--withoutTax")
            or soup.select_one(".price--main")
        )
        stock_el = (
            soup.select_one("[data-dotd-quantity]")
            or soup.select_one(".dotd-quantity")
            or soup.select_one(".alertBox--info")
        )

    title = title_el.get_text(strip=True) if title_el else None
    price = price_el.get_text(strip=True) if price_el else None
    stock = stock_el.get_text(strip=True) if stock_el else None

    if not title:
        print("Could not find deal title. Page might have changed structure.")
        print("Page preview:")
        print(soup.get_text()[:1000])
        sys.exit(1)

    return {"title": title, "price": price or "N/A", "stock": stock or "N/A"}


def notify(deal):
    body = f"{deal['title']}\nPrice: {deal['price']}\nIn Stock: {deal['stock']}"
    resp = requests.post(
        NTFY_URL,
        data=body.encode(),
        headers={
            "Title": "Game Nerdz Deal of the Day",
            "Tags": "video_game,moneybag",
        },
        timeout=10,
    )
    resp.raise_for_status()
    print(f"Notification sent!\n{body}")


def main():
    parser = argparse.ArgumentParser(description="Game Nerdz Deal of the Day notifier")
    parser.add_argument("--test", action="store_true", help="Send a test notification")
    args = parser.parse_args()

    deal = scrape_deal()

    if args.test:
        print("=== Deal of the Day ===")
        print(f"Item:  {deal['title']}")
        print(f"Price: {deal['price']}")
        print(f"Stock: {deal['stock']}")
        print("(test mode — notification not sent)")
        return

    notify(deal)


if __name__ == "__main__":
    main()

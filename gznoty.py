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
        # Wait a bit more for StorePass JS to render products
        page.wait_for_timeout(5000)

        # Dump the product area HTML so we can see the real structure
        debug = page.evaluate("""() => {
            const el = document.querySelector('.product-imports');
            if (el && el.innerHTML.trim().length > 0) return el.innerHTML.substring(0, 3000);
            // fallback: dump all classes on the page that mention product/stock/card
            const all = [...document.querySelectorAll('*')];
            const relevant = all.filter(e => {
                const cls = e.className?.toString() || '';
                return /product|stock|card|deal|price|inventory/i.test(cls);
            });
            return relevant.map(e => e.tagName + '.' + e.className + '=' + e.innerText?.substring(0, 100)).join('\\n');
        }""")

        browser.close()

    print(debug)


def main():
    scrape_deal()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Scraper module for sources without RSS feeds.
"""

import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


def fetch_html(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def scrape_influence(url: str = "https://www.influence.io/updates") -> list[dict]:
    """Scrapes product update items from influence.io/updates."""
    soup = fetch_html(url)
    results = []

    for a in soup.find_all("a", href=re.compile(r"^https://www\.influence\.io/updates/.+")):
        if "support.influence" in a.get("href", ""):
            continue
        href = a["href"].strip()

        # Walk up DOM to find h3 title
        parent = a.find_parent()
        h3 = None
        for _ in range(6):
            if parent is None:
                break
            h3 = parent.find("h3")
            if h3:
                break
            parent = parent.find_parent()

        title = h3.get_text(strip=True) if h3 else href.split("/")[-1].replace("-", " ").title()
        if title and href:
            results.append({"title": title, "url": href})

    seen = set()
    return [r for r in results if not (r["url"] in seen or seen.add(r["url"]))]


def scrape_voucherify(url: str = "https://docs.voucherify.io/changelog/changelog") -> list[dict]:
    """Scrapes changelog date entries from Voucherify."""
    soup = fetch_html(url)
    results = []
    base = "https://docs.voucherify.io/changelog/changelog"

    for h2 in soup.find_all("h2"):
        text = h2.get_text(strip=True)
        if not re.search(r"\d{4}|\d+(st|nd|rd|th)", text):
            continue
        anchor = h2.get("id", "")
        if not anchor:
            a = h2.find("a", id=True)
            anchor = a["id"] if a else ""
        full_url = f"{base}#{anchor}" if anchor else base
        results.append({"title": text, "url": full_url})

    seen = set()
    return [r for r in results if not (r["url"] in seen or seen.add(r["url"]))]


SCRAPERS = {
    "Influence.io": scrape_influence,
    "Voucherify": scrape_voucherify,
}

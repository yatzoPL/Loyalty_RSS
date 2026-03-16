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

BASE_INFLUENCE = "https://www.influence.io"


def fetch_html(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def dedupe(items: list[dict]) -> list[dict]:
    seen = set()
    return [i for i in items if not (i["url"] in seen or seen.add(i["url"]))]


# ---------------------------------------------------------------------------
# Influence.io
# ---------------------------------------------------------------------------
def scrape_influence(url: str = f"{BASE_INFLUENCE}/updates") -> list[dict]:
    """
    Each update block has:
    - A date text node near the top of the block
    - An h3 title
    - A 'More' link to /updates/<slug>
    Strategy: find all 'More' links, then walk up to find h3 and date.
    """
    soup = fetch_html(url)
    pattern = re.compile(r"(^/updates/.+|^https://www\.influence\.io/updates/.+)")
    results = []

    for a in soup.find_all("a", href=pattern):
        href = a.get("href", "").strip()
        if "support.influence" in href:
            continue

        # Normalise to absolute URL
        if href.startswith("/"):
            href = BASE_INFLUENCE + href

        # Walk up DOM to find h3 title and date
        parent = a.find_parent()
        h3 = None
        date_text = ""

        for _ in range(10):
            if parent is None:
                break
            if not h3:
                h3 = parent.find("h3")
            # Date is usually a plain text node or <p>/<div> near the block top
            # Look for text matching date pattern e.g. "October 10, 2025"
            if not date_text:
                for el in parent.find_all(text=re.compile(
                    r"(January|February|March|April|May|June|July|August|"
                    r"September|October|November|December)\s+\d{1,2},\s+\d{4}"
                )):
                    candidate = el.strip()
                    if candidate:
                        date_text = candidate
                        break
            if h3 and date_text:
                break
            parent = parent.find_parent()

        title = (
            h3.get_text(strip=True)
            if h3
            else href.split("/")[-1].replace("-", " ").title()
        )

        if title and href:
            results.append({
                "title": title,
                "url": href,
                "published": date_text,
            })

    return dedupe(results)


# ---------------------------------------------------------------------------
# LoyaltyLion
# ---------------------------------------------------------------------------
def scrape_loyaltylion(url: str = "https://loyaltylion.com/platform/product-updates") -> list[dict]:
    """
    Scrapes seasonal product update links from loyaltylion.com/platform/product-updates.
    Each entry is a link to a seasonal page like /platform/summer-2025-product-updates.
    """
    soup = fetch_html(url)
    pattern = re.compile(r"/platform/[a-z]+-\d{4}-product-updates")
    results = []

    for a in soup.find_all("a", href=pattern):
        href = a.get("href", "").strip()
        if href.startswith("/"):
            href = "https://loyaltylion.com" + href

        title = a.get_text(strip=True)
        if not title:
            # Derive title from URL slug e.g. summer-2025-product-updates
            slug = href.split("/platform/")[-1].replace("-", " ").title()
            title = f"LoyaltyLion: {slug}"

        if href:
            results.append({"title": title, "url": href})

    return dedupe(results)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
SCRAPERS = {
    "Influence.io": scrape_influence,
    "LoyaltyLion": scrape_loyaltylion,
}

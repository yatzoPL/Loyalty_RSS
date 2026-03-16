#!/usr/bin/env python3
"""
Scraper module for sources without RSS feeds.
Each scraper returns a list of dicts: {title, url}
"""

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

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


# ---------------------------------------------------------------------------
# Influence.io
# ---------------------------------------------------------------------------
def scrape_influence(url: str = "https://www.influence.io/updates") -> list[dict]:
    """
    Scrapes product update items from influence.io/updates.
    Each item has a h3 title and a 'More' link to /updates/<slug>.
    """
    soup = fetch_html(url)
    results = []

    # Find all 'More' links that point to /updates/<slug>
    for a in soup.find_all("a", href=re.compile(r"^https://www\.influence\.io/updates/.+")):
        # Skip support article links
        if "support.influence" in a.get("href", ""):
            continue

        href = a["href"].strip()

        # Find the closest h3 sibling or parent
        parent = a.find_parent()
        h3 = None
        # Walk up to find h3 in the same section
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

    # Deduplicate by URL
    seen = set()
    unique = []
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)

    return unique


# ---------------------------------------------------------------------------
# Talon One
# ---------------------------------------------------------------------------
def scrape_talon_one(url: str = "https://docs.talon.one/whats-new/product-updates") -> list[dict]:
    """
    Scrapes the list of monthly update links from Talon One docs.
    Each entry is a month/date link like /whats-new/2026/03/11.
    """
    soup = fetch_html(url)
    results = []

    base = "https://docs.talon.one"
    for a in soup.find_all("a", href=re.compile(r"^/whats-new/\d{4}/\d{2}/\d{2}$")):
        href = a["href"].strip()
        full_url = base + href
        title = a.get_text(strip=True) or href
        if title and full_url:
            results.append({"title": f"Talon One updates: {title}", "url": full_url})

    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)

    return unique


# ---------------------------------------------------------------------------
# Voucherify
# ---------------------------------------------------------------------------
def scrape_voucherify(url: str = "https://docs.voucherify.io/changelog/changelog") -> list[dict]:
    """
    Scrapes changelog entries from Voucherify.
    Each entry is a date heading (h2) with an anchor link.
    """
    soup = fetch_html(url)
    results = []

    base = "https://docs.voucherify.io/changelog/changelog"

    for h2 in soup.find_all("h2"):
        text = h2.get_text(strip=True)
        # Skip non-date headings like "Added", "Fixed" etc.
        if not re.search(r"\d{4}|\d+(st|nd|rd|th)", text):
            continue

        # Find anchor id
        anchor = h2.get("id") or ""
        if not anchor:
            a = h2.find("a", id=True)
            anchor = a["id"] if a else ""

        full_url = f"{base}#{anchor}" if anchor else base
        results.append({"title": f"Voucherify changelog: {text}", "url": full_url})

    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)

    return unique


# ---------------------------------------------------------------------------
# Registry – maps source name to scraper function
# ---------------------------------------------------------------------------
SCRAPERS = {
    "Influence.io": scrape_influence,
    "Talon One": scrape_talon_one,
    "Voucherify": scrape_voucherify,
}

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
BASE_VOUCHERIFY = "https://docs.voucherify.io/changelog/changelog"


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
    Links on the page are relative: /updates/<slug>
    We match both relative and absolute forms, then normalise to absolute.
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

        # Walk up DOM to find the h3 title for this entry
        parent = a.find_parent()
        h3 = None
        for _ in range(8):
            if parent is None:
                break
            h3 = parent.find("h3")
            if h3:
                break
            parent = parent.find_parent()

        title = (
            h3.get_text(strip=True)
            if h3
            else href.split("/")[-1].replace("-", " ").title()
        )
        if title and href:
            results.append({"title": title, "url": href})

    return dedupe(results)


# ---------------------------------------------------------------------------
# Voucherify
# ---------------------------------------------------------------------------
def scrape_voucherify(url: str = BASE_VOUCHERIFY) -> list[dict]:
    """
    Changelog entries are h2 headings with date text.
    The anchor id lives either on the h2 itself or on a child <a> tag.
    """
    soup = fetch_html(url)
    results = []

    for h2 in soup.find_all("h2"):
        text = h2.get_text(strip=True)

        # Keep only date-like headings
        if not re.search(r"\d{4}|\d+(st|nd|rd|th)", text):
            continue

        # Try to get anchor id from h2 or its child <a>
        anchor = h2.get("id", "")
        if not anchor:
            child_a = h2.find("a", id=True)
            if child_a:
                anchor = child_a["id"]
        if not anchor:
            # Last resort: slugify the text
            anchor = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

        full_url = f"{url}#{anchor}"
        results.append({"title": text, "url": full_url})

    return dedupe(results)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
SCRAPERS = {
    "Influence.io": scrape_influence,
    "Voucherify": scrape_voucherify,
}

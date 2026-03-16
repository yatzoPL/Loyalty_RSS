#!/usr/bin/env python3
import feedparser

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

urls = [
    "https://blog.smile.io/rss/",
    "https://antavo.com/feed/",
]

for url in urls:
    f = feedparser.parse(url, request_headers=headers)
    print(f"URL: {url}")
    print(f"  Status: {f.get('status', 'N/A')}")
    print(f"  Entries: {len(f.entries)}")
    if f.entries:
        e = f.entries[0]
        print(f"  First title: {e.get('title')}")
        print(f"  Tags: {[t.get('term') for t in e.get('tags', [])]}")
        print(f"  Category: {e.get('category')}")
    print()

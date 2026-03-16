#!/usr/bin/env python3
"""
RSS Daily Digest – Dotdigital
Checks configured RSS feeds for new articles and sends a daily email digest.
"""

import json
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import feedparser

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
SOURCES_FILE = BASE_DIR / "sources.json"
SEEN_FILE = BASE_DIR / "seen.json"

# ---------------------------------------------------------------------------
# Config from environment variables (set as GitHub Secrets)
# ---------------------------------------------------------------------------
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", GMAIL_USER)

# Try to look like a real browser to avoid 403s from some feeds
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_seen() -> dict:
    if SEEN_FILE.exists():
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_seen(seen: dict) -> None:
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, indent=2, ensure_ascii=False)


def fetch_feed(url: str) -> feedparser.FeedParserDict:
    return feedparser.parse(url, request_headers=HEADERS)


def entry_matches_category(entry: dict, category_filter: str) -> bool:
    """Check if an entry belongs to the required category."""
    tags = [t.get("term", "") for t in entry.get("tags", [])]
    cats = [entry.get("category", "")] + tags
    return any(category_filter.lower() in c.lower() for c in cats)


def get_new_entries(source: dict, seen_urls: set) -> list[dict]:
    """Fetch feed and return only entries not seen before."""
    feed = fetch_feed(source["feed_url"])
    entries = feed.entries

    # Fallback URL if primary returns nothing
    if not entries and source.get("fallback_feed_url"):
        print(f"  → primary empty, trying fallback feed…", end=" ")
        feed = fetch_feed(source["fallback_feed_url"])
        entries = feed.entries

    category_filter = source.get("category_filter")

    new_entries = []
    for entry in entries:
        url = entry.get("link", "")
        if not url or url in seen_urls:
            continue
        if category_filter and not entry_matches_category(entry, category_filter):
            continue

        new_entries.append({
            "title": entry.get("title", "(brak tytułu)"),
            "url": url,
            "published": entry.get("published", ""),
        })

    return new_entries


def build_html_email(updates: dict[str, list]) -> str:
    today = datetime.now(timezone.utc).strftime("%d.%m.%Y")
    total = sum(len(v) for v in updates.values())

    sections = ""
    for source_name, entries in updates.items():
        if not entries:
            continue
        items = ""
        for e in entries:
            title = e["title"].replace("<", "&lt;").replace(">", "&gt;")
            url = e["url"]
            pub = e.get("published", "")
            items += f"""
            <tr>
              <td style="padding:10px 0 10px 0;border-bottom:1px solid #f0f0f0;">
                <a href="{url}" style="color:#1a1a1a;font-weight:600;font-size:14px;
                   text-decoration:none;">{title}</a>
                {"<br><span style='color:#888;font-size:12px;'>" + pub + "</span>" if pub else ""}
              </td>
            </tr>"""

        sections += f"""
        <tr>
          <td style="padding:20px 0 4px 0;">
            <span style="font-size:11px;font-weight:700;letter-spacing:1px;
              color:#888;text-transform:uppercase;">{source_name}</span>
          </td>
        </tr>
        {items}
        """

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:32px 16px;">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:8px;overflow:hidden;">

        <tr>
          <td style="background:#1a1a1a;padding:24px 32px;">
            <span style="color:#ffffff;font-size:18px;font-weight:700;">
              📬 Loyalty Tech Updates
            </span>
            <br>
            <span style="color:#aaa;font-size:12px;">{today} · {total} nowych artykułów</span>
          </td>
        </tr>

        <tr>
          <td style="padding:8px 32px 32px 32px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              {sections}
            </table>
          </td>
        </tr>

        <tr>
          <td style="background:#f9f9f9;padding:16px 32px;border-top:1px solid #eee;">
            <span style="color:#bbb;font-size:11px;">
              Dotdigital RSS Digest · generowany automatycznie
            </span>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send_email(subject: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        sources = json.load(f)

    seen = load_seen()
    updates: dict[str, list] = {}

    for source in sources:
        name = source["name"]
        seen_urls = set(seen.get(name, []))

        print(f"Checking: {name} …", end=" ")
        try:
            new_entries = get_new_entries(source, seen_urls)
        except Exception as exc:
            print(f"ERROR – {exc}")
            continue

        print(f"{len(new_entries)} new")

        if new_entries:
            updates[name] = new_entries
            seen[name] = list(seen_urls | {e["url"] for e in new_entries})

    if not updates:
        print("No new articles. No email sent.")
        save_seen(seen)
        return

    total = sum(len(v) for v in updates.values())
    subject = f"📬 Dotdigital: {total} nowych artykułów ({datetime.now().strftime('%d.%m.%Y')})"
    html = build_html_email(updates)

    print(f"Sending email: {subject}")
    send_email(subject, html)
    print("Email sent.")

    save_seen(seen)


if __name__ == "__main__":
    main()

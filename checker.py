#!/usr/bin/env python3
"""
RSS + Scraper Daily Digest – Dotdigital Loyalty
"""

import json
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import feedparser

BASE_DIR = Path(__file__).parent
SOURCES_FILE = BASE_DIR / "sources.json"
SEEN_FILE = BASE_DIR / "seen.json"

GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", GMAIL_USER)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


def load_seen() -> dict:
    if SEEN_FILE.exists():
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_seen(seen: dict) -> None:
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, indent=2, ensure_ascii=False)


def get_new_rss_entries(source: dict, seen_urls: set) -> list[dict]:
    feed = feedparser.parse(source["feed_url"], request_headers=HEADERS)
    entries = feed.entries

    if not entries and source.get("fallback_feed_url"):
        feed = feedparser.parse(source["fallback_feed_url"], request_headers=HEADERS)
        entries = feed.entries

    category_filter = source.get("category_filter")
    new_entries = []

    for entry in entries:
        url = entry.get("link", "")
        if not url or url in seen_urls:
            continue
        if category_filter:
            tags = [t.get("term", "") for t in entry.get("tags", [])]
            cats = [entry.get("category", "")] + tags
            if not any(category_filter.lower() in c.lower() for c in cats):
                continue
        new_entries.append({
            "title": entry.get("title", "(no title)"),
            "url": url,
            "published": entry.get("published", ""),
        })

    return new_entries


def get_new_scraped_entries(source: dict, seen_urls: set) -> list[dict]:
    from scrapers import SCRAPERS
    scraper_fn = SCRAPERS.get(source["scraper"])
    if not scraper_fn:
        raise ValueError(f"Unknown scraper: {source['scraper']}")

    all_entries = scraper_fn()
    return [
        {"title": e.get("title", "(no title)"), "url": e["url"], "published": ""}
        for e in all_entries
        if e.get("url") and e["url"] not in seen_urls
    ]


def build_html_email(updates: dict) -> str:
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
              Loyalty Tech Updates
            </span>
            <br>
            <span style="color:#aaa;font-size:12px;">{today} &middot; {total} new items</span>
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
              Dotdigital Loyalty RSS Digest &middot; auto-generated
            </span>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send_email(subject: str, html_body: str) -> None:
    recipients = [r.strip() for r in RECIPIENT_EMAIL.split(",") if r.strip()]
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, recipients, msg.as_string())


def main() -> None:
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        sources = json.load(f)

    seen = load_seen()
    updates = {}

    for source in sources:
        name = source["name"]
        seen_urls = set(seen.get(name, []))

        print(f"Checking: {name} ...", end=" ")
        try:
            if source.get("type") == "scraper":
                new_entries = get_new_scraped_entries(source, seen_urls)
            else:
                new_entries = get_new_rss_entries(source, seen_urls)
        except Exception as exc:
            print(f"ERROR - {exc}")
            continue

        print(f"{len(new_entries)} new")

        if new_entries:
            updates[name] = new_entries
            seen[name] = list(seen_urls | {e["url"] for e in new_entries})

    if not updates:
        print("No new items. No email sent.")
        save_seen(seen)
        return

    total = sum(len(v) for v in updates.values())
    subject = f"What's New in Loyalty? | Daily Digest: {total} new items ({datetime.now().strftime('%d.%m.%Y')})"
    html = build_html_email(updates)

    print(f"Sending email: {subject}")
    send_email(subject, html)
    print("Email sent.")

    save_seen(seen)


if __name__ == "__main__":
    main()

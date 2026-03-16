# Loyalty Tech Weekly Digest

Automated weekly email digest monitoring product updates from loyalty tech platforms. Runs every Tuesday at 09:00 Warsaw time via GitHub Actions.

## Sources

| Source | Type | URL |
|--------|------|-----|
| Smile.io | RSS | `https://blog.smile.io/rss/` |
| Antavo | RSS | `https://antavo.com/feed/` |
| Talon One | RSS | `https://docs.talon.one/whats-new/rss.xml` |
| Voucherify | RSS | `https://docs.voucherify.io/changelog/changelog/rss.xml` |
| LoyaltyLion | Scraper | `https://loyaltylion.com/platform/product-updates` |
| Influence.io | Scraper | `https://www.influence.io/updates` |

## File Structure

```
├── checker.py          # Main script – checks feeds, sends email
├── scrapers.py         # Scraper functions for non-RSS sources
├── sources.json        # Source configuration
├── seen.json           # State file – tracks already-seen URLs (auto-updated)
├── requirements.txt    # Python dependencies
└── .github/
    └── workflows/
        └── rss-digest.yml  # GitHub Actions workflow (runs every Tuesday)
```

## Setup

### 1. Create a private GitHub repository and upload all files.

### 2. Generate a Gmail App Password

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Enable 2-Step Verification if not already active
3. Generate a new App Password (name it e.g. "RSS Digest")
4. Copy the 16-character code

### 3. Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Value |
|--------|-------|
| `GMAIL_USER` | your Gmail address |
| `GMAIL_APP_PASSWORD` | 16-character App Password from step 2 |
| `RECIPIENT_EMAIL` | recipient email address |

### 4. Enable workflow write permissions

Go to **Settings → Actions → General → Workflow permissions** → select **Read and write permissions** → Save.

### 5. Test manually

Go to **Actions → RSS Daily Digest → Run workflow**.

On first run you will receive all historical items from each source. From the second run onwards, only new items are sent.

## How It Works

1. GitHub Actions triggers `checker.py` every Tuesday at 07:00 UTC
2. Script fetches each RSS feed or scrapes each page
3. Compares results against `seen.json` (previously seen URLs)
4. If new items found → sends HTML email digest
5. Updates `seen.json` and commits it back to the repository

## Adding a New Source

### RSS source – add to `sources.json`:
```json
{
  "name": "Source Name",
  "type": "rss",
  "feed_url": "https://example.com/feed",
  "category_filter": null
}
```

### Scraper source – add a function to `scrapers.py`, register it in `SCRAPERS`, then add to `sources.json`:
```json
{
  "name": "Source Name",
  "type": "scraper",
  "scraper": "Source Name"
}
```

## Dependencies

- `feedparser` – RSS/Atom feed parsing
- `requests` – HTTP requests for scrapers
- `beautifulsoup4` – HTML parsing for scrapers

# RSS Daily Digest

Automatyczny codzienny email z nowymi artykułami z monitorowanych źródeł loyalty tech.

## Struktura plików

```
rss-digest/
├── checker.py          # Główny skrypt
├── sources.json        # Lista źródeł RSS
├── seen.json           # Stan (które URL już widziano) – generowany automatycznie
├── requirements.txt    # Zależności Python
└── .github/
    └── workflows/
        └── rss-digest.yml  # GitHub Actions – uruchamia skrypt codziennie o 7:00 UTC
```

## Setup (jednorazowy)

### 1. Utwórz repozytorium na GitHub

Utwórz **prywatne** repozytorium i wgraj wszystkie pliki.

### 2. Wygeneruj Gmail App Password

1. Wejdź na [myaccount.google.com/security](https://myaccount.google.com/security)
2. Włącz **2-Step Verification** (jeśli nie jest włączona)
3. Przejdź do **App passwords** → wybierz "Mail" + "Other" → wpisz nazwę np. "RSS Digest"
4. Skopiuj wygenerowane 16-znakowe hasło

### 3. Dodaj GitHub Secrets

W repozytorium: **Settings → Secrets and variables → Actions → New repository secret**

Dodaj trzy sekrety:

| Nazwa | Wartość |
|-------|---------|
| `GMAIL_USER` | twój.email@gmail.com |
| `GMAIL_APP_PASSWORD` | 16-znakowe hasło z kroku 2 |
| `RECIPIENT_EMAIL` | email odbiorcy (może być ten sam) |

### 4. Uruchom ręcznie (test)

W repozytorium: **Actions → RSS Daily Digest → Run workflow**

Jeśli są nowe artykuły – dostaniesz emaila. Jeśli nie ma nic nowego – brak emaila (to prawidłowe zachowanie).

## Jak to działa

1. GitHub Actions uruchamia `checker.py` codziennie o 9:00 czasu warszawskiego
2. Skrypt pobiera RSS każdego źródła
3. Porównuje z `seen.json` (lista już widzianych URL)
4. Jeśli są nowe artykuły → wysyła HTML email
5. Aktualizuje `seen.json` i commituje z powrotem do repo

## Monitorowane źródła (etap 1 – RSS)

| Źródło | Feed URL |
|--------|----------|
| Loyalty Lion | `https://app.getbeamer.com/loyaltylion/en?rss=true` |
| Smile.io | `https://blog.smile.io/tag/smile-updates/rss/` (tylko kategoria smile-updates) |
| Antavo | `https://antavo.com/feed/` |

## Dodawanie nowych źródeł

Edytuj `sources.json` i dodaj obiekt:

```json
{
  "name": "Nazwa źródła",
  "feed_url": "https://przyklad.com/feed",
  "filter": null
}
```

## Etap 2 (scraping – planowane)

Źródła bez RSS do dodania w kolejnym etapie:
- Influence.io (`/updates`)
- Talon One (`docs.talon.one/whats-new/product-updates`)
- Voucherify (`docs.voucherify.io/changelog/changelog`)

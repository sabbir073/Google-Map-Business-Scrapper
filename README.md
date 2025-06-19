# Google-Maps Business Scraper

A Python CLI that behaves like a real person on Google Maps:  
it scrolls the left-hand results panel, clicks every listing, opens the
detail pane, and stores **country, city, business type, name, website,
phone, reviews, address, Maps URL, first email found on the
business site** straight into Google Sheets.

---

## 1 · Tech stack

| Layer | Library / Tool | Reason |
|-------|----------------|--------|
| Browser automation | **Selenium 4** (non-headless Chrome, CDP) | Human-like scrolling & clicking |
| Data store | **Google Sheets API v4** | Easy sharing, zero DB setup |
| HTML parsing | **BeautifulSoup 4 + requests** | Grab first `mailto:` or “@” on the business website |
| Config | **python-dotenv** | One-file runtime configuration (`.env`) |
| Packaging | `requirements.txt` + optional **virtual env** | Simple pip workflow |

---

## 2 · Demo `.env`

```env
# ── Google Sheets ────────────────────────────────────────────────
INPUT_SHEET_ID=***************************
OUTPUT_SHEET_ID=**************************
INPUT_TAB=Sheet1         # default "Input"
OUTPUT_TAB=Sheet1        # default "Scraped"

# ── Service-account JSON ─────────────────────────────────────────
SERVICE_ACCOUNT_FILE=credentials/service_account.json

# ── Chrome tweaks (optional) ─────────────────────────────────────
# CHROME_EXECUTABLE=/usr/bin/google-chrome
CDP_PORT=9222

# ── Runtime knobs ────────────────────────────────────────────────
MAX_RESULTS_PER_SEARCH=150
LOG_LEVEL=INFO            # DEBUG | INFO | WARNING | ERROR | CRITICAL
DELAY_RANGE=2,4           # min,max seconds (randomised human delay)

# ── Proxy example ────────────────────────────────────────────────
# HTTPS_PROXY=http://user:pass@proxy-ip:port
```

> **Do not commit your `.env` or `service_account.json`.**  
> The provided `.gitignore` already protects them.

---

## 3 · Install & run

```bash
git clone https://github.com/sabbir073/Google-Map-Business-Scrapper
cd Google-Map-Business-Scrapper

python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# drop service_account.json into ./credentials/
# create your .env (use the demo above)

python -m app.main --max 150 --log INFO
```

Console output:

```
INFO  🚀 Launching Chrome …
INFO  🔍  United States | Tampa, FL | Legal Services
INFO     ↳ 42 businesses scraped
INFO  ✅ 39 new rows saved to output sheet
```

Open the **output** sheet’s *Scraped* tab — freshly scraped rows are waiting.

---

## 4 · Roadmap & ideas

| Planned | Why it’s useful |
|---------|-----------------|
| **Deep-crawl email hunt** | Visit `/contact`, `/about`, secondary pages; integrate Hunter/Snov for enrichment. |
| **Proxy rotation** | Scale to thousands of cities without CAPTCHAs or IP throttling. |
| **Docker image** | One-liner deployment: `docker run -v $PWD/.env:/app/.env maps-scraper`. |
| **Resume / checkpoint** | Persist queue so long scrapes survive crashes or reboots. |
| **Headless-stealth toggle** | Optional fully headless mode with anti-bot fingerprints patched. |
| **Web dashboard** | Trigger jobs, monitor progress, download CSVs from a small Flask UI. |
| **Geo-targeted proxies** | Route each search via a proxy in the target country for more local results. |

Pull requests welcome 🤝 — feel free to extend the scraper in any of these directions.

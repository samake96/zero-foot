# ZERO FOOT V3 — RSS headlines prototype

Static bilingual football site with an automated external-headline feed. Existing scores and forecasts are **fictional demo data**, not live. The RSS feed is **not yet populated**.

## Run

1. With internet access, run `python3 scripts/update_news.py` to fetch BBC Sport Football and The Guardian Football RSS headline metadata.
2. Serve the project directory with `python3 -m http.server 8000` and open `http://localhost:8000`. Opening `index.html` directly via `file://` may block JSON fetching.
3. Host the folder on GitHub Pages or another static host. GitHub Actions `.github/workflows/news.yml` attempts updates every 3 hours (scheduled execution may be delayed or disabled). Set GitHub Actions workflow permissions to allow writes where needed.

## Editorial and licensing

The feed stores headlines, URLs, publication dates and publisher names only; articles remain on the original sites. Confirm each source's RSS terms and commercial reuse rights before monetization. RSS headlines are displayed in their original English, even when the site UI is French; automated translation is **not** implemented. Do not claim that RSS headlines are original ZERO FOOT journalism. Build human-reviewed original match analysis and legal/privacy/contact pages before AdSense application. Never publish invented scores or prediction accuracy claims.

If every feed fails, the collector preserves the last successful feed. This project has no live server, no paid data license, no AdSense approval, and no verified public deployment.

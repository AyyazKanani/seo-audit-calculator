# SEO Audit Calculator

A Django 5 SaaS web app that scores any webpage for on-page SEO, explains what to fix, and exports a branded PDF report. Includes email + Google login, a personal dashboard, report history, a URL analyzer that fetches live pages, and an AI SEO assistant.

**Repo:** https://github.com/AyyazKanani/seo-audit-calculator

---

## What it does

- **Manual SEO audit** — paste a URL, title, meta description, page content, and target keyword → get scores out of 100 for Title, Meta, URL, Content, and Keyword Density, plus a weighted Overall score (A/B/C/D grade) and fix-it recommendations.
- **URL Analyzer** — paste any public URL → the app fetches the real HTML, extracts title, meta, H1/H2, images, links, word count, HTTPS, canonical and robots tags, then scores it with the same engine. No dummy data — everything comes from the fetched page.
- **PDF export** — one-click branded PDF report (ReportLab) with grade-colored cards.
- **Auth** — email/password register, login, logout, profile, change password, forgot password + Google OAuth (django-allauth, same-window redirect with `next` support).
- **Dashboard** — total audits, average score, grade distribution, and 5 recent reports (2 queries).
- **Report history** — private per-user list with search, grade filter, pagination, and delete.
- **AI SEO assistant** — chat UI with keyword-matched answers and a swappable provider (`BaseAIProvider` → `DummyProvider` now, Gemini/OpenAI later).

## Tech stack

Python 3.12 · Django 5.2 · SQLite (dev) / PostgreSQL (prod) · django-allauth (Google OAuth) · BeautifulSoup4 + requests (URL analyzer) · ReportLab (PDF) · WhiteNoise + Gunicorn (prod static/server) · django-environ (.env config) · Bootstrap 5 + Bootstrap Icons + AOS animations

## How the scoring works

Weights (see `calculator/constants.py`): Title 25% · Content 25% · Meta 20% · URL 15% · Keyword 15%.

- Title: ideal 50–60 chars, contains keyword, 4–12 words.
- Meta description: ideal 120–160 chars, contains keyword.
- URL: short, hyphenated, lowercase, keyword slug, no query strings.
- Content: 600–1500 words ideal, keyword density 1–2.5% ideal.
- Grades: A (80–100) · B (60–79) · C (40–59) · D (0–39).

URL Analyzer extras: missing H1 check, images missing alt text, internal/external link counts, HTTPS check, canonical tag check, `noindex`/`nofollow` warnings.

## Security notes

- URL fetcher blocks SSRF: only `http(s)`, rejects localhost / private / reserved IPs, re-checks redirect targets, enforces 5 MB + 10 s limits, and only accepts HTML content.
- Report views enforce ownership (IDOR-safe). Production settings enable HTTPS redirect, HSTS, and secure cookies.

## Project structure

```
seo_audit/          # settings, urls, wsgi
core/               # homepage, landing
accounts/           # email auth views + Google OAuth wiring
calculator/         # SEOReport model, scoring engine, PDF, manual audit views
  analyzer/         # URL analyzer: fetcher.py, parser.py, scoring.py, views.py
dashboard/          # user stats dashboard
assistant/          # AI chat views + provider abstraction
templates/          # Bootstrap 5 dark SaaS theme
static/             # css, js, favicon
test_analyzer.py    # 10 URL-analyzer checks (run with: python test_analyzer.py)
test_oauth_flow.py  # 16 OAuth/UI regression checks (run with: python test_oauth_flow.py)
```

## Run it locally

You need Python 3.12 and Git.

```bash
# 1. Clone and enter the folder
git clone https://github.com/AyyazKanani/seo-audit-calculator.git
cd seo-audit-calculator

# 2. Create and activate a virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# 3. Install packages
pip install -r requirements.txt

# 4. Copy .env.example to .env and fill in your keys
copy .env.example .env
# Required: DJANGO_SECRET_KEY. Optional: GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET.

# 5. Set up the database
python manage.py migrate

# 6. Start the server
python manage.py runserver
```

Open http://127.0.0.1:8000/

Key pages: `/calculator/` (manual audit) · `/calculator/analyze/` (URL analyzer) · `/dashboard/` · `/assistant/` · `/accounts/login/`

## What I built and learned

- Full Django project: models, QuerySets, class/function views, forms, templates, auth, admin.
- Real-world OAuth debugging: fixed a popup-window login bug by switching to same-window redirect and threading the `next` parameter through login → Google → dashboard/calculator.
- Web scraping safely: SSRF protection, redirect validation, size/timeout limits, BeautifulSoup extraction.
- Clean architecture: pure scoring functions (no Django imports) reused by both the manual calculator and the URL analyzer; thin views + service layer.
- Testing: 26 script-based checks covering SSRF blocks, parsing, scoring with/without keywords, and OAuth redirects.

## Future improvements

- JavaScript-rendered page support (headless browser fallback).
- Real AI provider (Gemini/OpenAI) behind the existing `BaseAIProvider` interface.
- Scheduled re-audits + score-over-time charts.

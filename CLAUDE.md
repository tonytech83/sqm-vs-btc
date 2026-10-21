# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Flask app comparing the average price per m² of real estate in Sofia with the BTC/EUR price. One row per day is stored in PostgreSQL; the frontend charts the history with Chart.js.

## Commands

```sh
pip install -r requirements.txt
flask run                      # or: python app.py  (honors $PORT, default 5000)
gunicorn -c gunicorn_config.py app:app   # production-style (1 sync worker, 120s timeout)
pytest                         # all tests
pytest tests/test_app.py::TestDataView::test_data_view   # single test
```

There is no linter config in the repo. The tests in `tests/test_app.py` are integration tests against the real Flask app: they hit a live PostgreSQL and live external APIs (no mocks), so they need the env vars below. `/update-db` is called by a test and **writes to the configured database**.

## Configuration

Env vars are loaded from `.env` at the project root (`WebApp/helpers.py` calls `load_dotenv` on import):

- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: PostgreSQL connection
- `API_KEY`: sent as `x-api-key` to the private scraper API.

## Architecture

- `app.py` creates the Flask app and registers the class-based views (`flask.views.View`) with `add_url_rule`.
- `WebApp/views.py` has three routes:
  - `/` renders `templates/index.html` from the **latest DB row** (`get_latest_prices`), not from live prices.
  - `/data` returns all DB rows ordered by date as JSON, uncached. `static/js/chart.js` fetches it and builds every chart tab on the client: tabs come from the `VIEWS` table, and the time-range filter and the "growth = 100" rebasing also happen there. NUMERIC columns arrive as strings, and the JS converts them to numbers.
  - `/update-db` runs `get_prices_and_ratio()`. It creates the `data` table if needed, skips if today's UTC date already exists, otherwise fetches both prices and inserts `ratio = sqm_price / btc_price`. It returns `{"status": "inserted" | "exists" | "failed"}`, with HTTP 500 on `failed`.
- `WebApp/helpers.py` holds all DB access (`_connect()` opens a new `psycopg2` connection per call) and the price fetching. Fetch functions catch their own errors and return `None` instead of raising.
  - The sqm price comes from a private scraper service (`https://scraper-api.tonytech.xyz/sqm-price`, field `avg_price`). The app itself does no scraping.
  - BTC price: Binance first, then Kraken as fallback (`get_btc_price_in_eur`).
- Schema: table `data(id, date TEXT UNIQUE 'YYYY-MM-DD', btc_price, sqm_price, ratio)`.

## Deployment / scheduled jobs

Hosted on Render (`https://sqm-vs-btc.onrender.com`). The Dockerfile (python:3.10-slim) runs gunicorn on port 5000. GitHub Actions workflows:

- `main.yml` deploys to Render on push to `main`. The build and test jobs are commented out, so CI runs no tests.
- `insert_into_db.yml` curls `/update-db` daily at 00:00 UTC with `curl -f`, so a `failed` status turns the run red. This is the only thing that populates the DB.
- `keep_it_alive.yml` pings `/` and `/data` every 10 minutes to keep the free Render instance awake.

Python 3.10+ is required (the code uses `X | None` hints). The DB driver is `psycopg2-binary`, so no `pg_config` or libpq-dev is needed.

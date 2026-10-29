import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg2 as db
import requests
from dotenv import load_dotenv
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor, RealDictRow

# Always load the .env file from the project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "")


def _connect() -> connection:
    """Opens a new PostgreSQL connection using the DB_* environment variables."""
    return db.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )


def prepare_json() -> list[dict]:
    """
    Retrieves all entries from the database, oldest first.

    Returns:
        List[Dict]: A list of database entries as dictionaries.
        Returns an empty list if there's an error.

    """
    conn = None
    try:
        conn = _connect()
        cursor: RealDictCursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(query="SELECT * FROM data ORDER BY date")
        db_entries: list[RealDictRow] = cursor.fetchall()

        logger.info("Fetched %s entries from the database.", len(db_entries))

    except db.Error:
        logger.exception("Database error")
        return []

    else:
        return db_entries
    finally:
        if conn is not None:
            conn.close()


def get_latest_prices() -> RealDictRow | None:
    """
    Retrieves the latest entry from the database.

    Returns:
        Dict: The latest database entry containing btc_price and sqm_price.
        Returns None if there's an error or no entries exist.

    """
    conn = None
    try:
        conn = _connect()
        cursor: RealDictCursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(query="SELECT * FROM data ORDER BY date DESC LIMIT 1")
        latest_entry: RealDictRow | None = cursor.fetchone()

    except db.Error:
        logger.exception("Database error")
        return None
    else:
        return latest_entry
    finally:
        if conn is not None:
            conn.close()


def get_sqm_price_in_eur() -> float | None:
    """
    Calls the private scraper API for the current SQM average price expressed in EUR.

    Returns:
        float | None: Latest SQM price when the request succeeds; otherwise None.
        Network/HTTP/JSON errors are logged and swallowed to keep caller resilient.

    """
    url = API_URL
    headers = {
        "x-api-key": os.getenv("API_KEY"),
    }

    try:
        response = requests.get(url, timeout=60, headers=headers)
        response.raise_for_status()  # raises if HTTP 4xx/5xx

        data = response.json()
        avg_price = float(data["avg_price"])

    except Exception:
        logger.exception(msg="Failed to fetch sqm price from private API")
        return None

    else:
        return avg_price


def get_btc_price_binance() -> float | None:
    """
    Fetches the latest BTC/EUR price from Binance public API.

    Endpoint: `https://api.binance.com/api/v3/ticker/price?symbol=BTCEUR`

    Returns:
        float | None: Latest BTC price in EUR when available; otherwise None.
        Network/HTTP errors and unexpected response shapes are caught and logged.

    """
    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCEUR"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data["price"])
    except (requests.RequestException, KeyError, TypeError, ValueError):
        logger.exception(msg="Error fetching BTC price from Binance")
        return None


def get_btc_price_kraken() -> float | None:
    """
    Fetches the latest BTC/EUR price from Kraken public API.

    Endpoint: `https://api.kraken.com/0/public/Ticker?pair=XBTEUR`

    Returns:
        float | None: Latest BTC price in EUR when available; otherwise None.
        Network/HTTP errors and unexpected response shapes are caught and logged.

    """
    url = "https://api.kraken.com/0/public/Ticker?pair=XBTEUR"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data["result"]["XXBTZEUR"]["c"][0])
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
        logger.exception(msg="Error fetching BTC price from Kraken")
        return None


def get_btc_price_in_eur() -> float | None:
    """
    Returns the first successfully retrieved BTC/EUR price from multiple sources.

    Strategy:
    - Tries Binance, then Kraken in order.
    - Logs the selected source and price when successful; logs an error if all fail.

    Returns:
        float | None: BTC price in EUR if any source succeeds; otherwise None.

    """
    for source in [get_btc_price_binance, get_btc_price_kraken]:
        price: float | None = source()
        if price:
            logger.info("BTC Price from %s: %s EUR", source.__name__, price)
            return price
    logger.error("Failed to fetch BTC price from all sources.")
    return None


def get_prices_and_ratio() -> str:
    """
    Fetches current BTC and square meter prices, calculates their ratio, and stores the data in the database.

    The function:
    1. Creates the data table if it doesn't exist
    2. Checks for existing entry for today
    3. Fetches current prices
    4. Calculates the ratio
    5. Stores the new entry

    Returns:
        str: "inserted" when today's entry was added, "exists" when it was already
        there, or "failed" when a price could not be fetched or the database failed.

    """
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS data (
                id SERIAL PRIMARY KEY,
                date TEXT NOT NULL UNIQUE,
                btc_price NUMERIC(18, 8) NOT NULL,
                sqm_price NUMERIC(18, 8) NOT NULL,
                ratio NUMERIC(20, 18) NOT NULL
            )
            """,
        )
        conn.commit()

        # Check if today's entry already exists
        today: str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        cursor.execute("SELECT 1 FROM data WHERE date = %s", (today,))
        if cursor.fetchone():
            logger.info("Entry for %s already exists. Skipping.", today)
            return "exists"

        sqm_price: float | None = get_sqm_price_in_eur()
        btc_price: float | None = get_btc_price_in_eur()

        if sqm_price is None or btc_price is None:
            logger.error("Failed to fetch data. Skipping database insertion.")
            return "failed"

        ratio: float = sqm_price / btc_price

        cursor.execute(
            """
            INSERT INTO data (date, btc_price, sqm_price, ratio)
            VALUES(%s, %s, %s, %s)
            ON CONFLICT (date) DO NOTHING
            """,
            (today, btc_price, sqm_price, ratio),
        )
        conn.commit()
        logger.info("Added new entry for %s", today)
    except db.Error:
        logger.exception("Database error")
        return "failed"
    else:
        return "inserted"
    finally:
        if conn is not None:
            conn.close()

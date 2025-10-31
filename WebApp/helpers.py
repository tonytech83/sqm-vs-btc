import logging
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import psycopg2 as db
import requests
from bs4 import BeautifulSoup
from psycopg2.extras import RealDictCursor, RealDictRow
from requests.models import Response

if TYPE_CHECKING:
    from bs4.element import ResultSet
    from flask import Response

logger = logging.getLogger(__name__)
logger.info("Foobar")


def prepare_json() -> list[dict]:
    """
    Retrieves all entries from the database and returns them as a list of dictionaries.

    Returns:
        List[Dict]: A list of database entries as dictionaries.
        Returns an empty list if there's an error.

    Note:
        Uses RealDictCursor for dictionary-style results.
        Automatically closes database connection in finally block.

    """
    # Initialize conn to None
    conn = None
    try:
        conn = db.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
        )
        # Use RealDictCursor for dict rows
        cursor: RealDictCursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(query="SELECT * FROM data")
        # Fetch rows as dictionaries
        db_entries: list[RealDictRow] = cursor.fetchall()

        # Debugging: Log the number of entries fetched
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
        conn = db.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
        )
        cursor: RealDictCursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(query="SELECT * FROM data ORDER BY id DESC LIMIT 1")
        latest_entry: RealDictRow | None = cursor.fetchone()

    except db.Error:
        logger.exception("Database error")
        return None
    else:
        return latest_entry
    finally:
        if conn is not None:
            conn.close()


def get_proxies_as_dict() -> dict[int, str]:
    """
    Fetches a list of public HTTPS proxies and returns them as a dict usable by requests.

    Source:
        https://www.proxy-list.download/api/v1/get?type=https

    Returns:
        dict[int, str]: Mapping of 1-based index to proxy URL with the https scheme
        (e.g., {1: "https://ip:port", 2: "https://ip:port", ...}). May raise on
        non-2xx responses.

    Notes:
        The returned mapping is passed directly to `requests.get(..., proxies=...)`.
        This function does not perform validation of proxy liveness.

    """
    response = requests.get(
        "https://www.proxy-list.download/api/v1/get?type=https",
        timeout=10,
    )

    response.raise_for_status()

    # split the response
    lines = response.text.strip().split("\n")

    # create a dict with index
    proxies = {
        i + 1: f"https://{line.strip()}" for i, line in enumerate(lines) if line.strip()
    }

    return proxies


def get_sqm_price_in_eur() -> float:
    """
    Scrapes the average residential price per square meter (EUR) from imoti.net.

    Implementation details:
    - Retrieves a set of public HTTPS proxies via `get_proxies_as_dict` and uses
      them with `requests` to fetch `https://www.imoti.net/bg/sredni-ceni`.
    - Parses the price table and computes the arithmetic mean of the values in the
      second column.

    Returns:
        float | None: The average price per square meter in EUR if parsing succeeds;
        otherwise None. Errors are logged.

    """
    proxies = get_proxies_as_dict()

    url = "https://www.imoti.net/bg/sredni-ceni"

    try:
        response = requests.get(url, timeout=60, proxies=proxies)
        soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")
        price_per_sqm_rows: ResultSet[Any] | Any = soup.find("tbody").find_all("tr")

        total_price = 0
        count = 0
        for row in price_per_sqm_rows:
            cells = row.find_all("td")
            if len(cells) > 1:
                price_cell: Any = cells[1].get_text(strip=True).replace(" ", "")
                try:
                    price: float = float(price_cell)
                    total_price += price
                    count += 1
                except ValueError:
                    continue

        return total_price / count if count > 0 else None

    except Exception:
        logger.exception(msg="Failed to fetch sqm price via ScraperAPI")
        return None


def get_btc_price_binance() -> float | None:
    """
    Fetches the latest BTC/EUR price from Binance public API.

    Endpoint: `https://api.binance.com/api/v3/ticker/price?symbol=BTCEUR`

    Returns:
        float | None: Latest BTC price in EUR when available; otherwise None.
        Network/HTTP errors are caught and logged.

    """
    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCEUR"
    try:
        response: Response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data["price"])
    except requests.RequestException:
        logger.exception(msg="Error fetching BTC price from Binance")
        return None


def get_btc_price_kraken() -> float | None:
    """
    Fetches the latest BTC/EUR price from Kraken public API.

    Endpoint: `https://api.kraken.com/0/public/Ticker?pair=XBTEUR`

    Returns:
        float | None: Latest BTC price in EUR when available; otherwise None.
        Network/HTTP errors are caught and logged.

    """
    url = "https://api.kraken.com/0/public/Ticker?pair=XBTEUR"
    try:
        response: Response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data["result"]["XXBTZEUR"]["c"][0])
    except requests.RequestException:
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
    logger.exception(msg="Failed to fetch BTC price from all sources.")
    return None


def get_prices_and_ratio() -> None:
    """
    Fetches current BTC and square meter prices, calculates their ratio, and stores the data in the database.

    The function:
    1. Creates the data table if it doesn't exist
    2. Checks for existing entry for today
    3. Fetches current prices
    4. Calculates the ratio
    5. Stores the new entry

    Note:
        - Skips insertion if an entry for today already exists
        - Uses ON CONFLICT DO NOTHING for date uniqueness
        - Automatically closes database connection in finally block
        - Logs all significant events and errors

    """
    conn = None  # Initialize conn to None
    try:
        conn = db.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
        )
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

        # Check if today's entry already exists
        today: str = datetime.now(tz=timezone.utc).strftime("%d %b %Y")
        cursor.execute("SELECT 1 FROM data WHERE date = %s", (today,))
        if cursor.fetchone():
            logger.info("Entry for %s already exists. Skipping.", today)
            return

        # Fetch current prices if not already fetched for today
        sqm_price: float = get_sqm_price_in_eur()
        btc_price: float | None = get_btc_price_in_eur()

        if sqm_price is None or btc_price is None:
            logger.exception("Failed to fetch data. Skipping database insertion.")
            return

        ratio: float = sqm_price / btc_price

        cursor.execute(
            """
            INSERT INTO data (date, btc_price, sqm_price, ratio)
            VALUES(%s, %s, %s, %s)
            ON CONFLICT (date) DO NOTHING
            """,
            (today, btc_price, sqm_price, ratio),
        )
        logger.info("Added new entry for %s", today)

        conn.commit()
    except db.Error:
        logger.exception("Database error")
    finally:
        if conn is not None:
            conn.close()


get_prices_and_ratio()

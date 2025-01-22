import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3 as db
import logging


def get_sqm_price_in_eur() -> float:
    """
    Scrapes the average square meter price in EUR from imoti.net for properties in Sofia.

    Returns:
        float: The average price per square meter in EUR.
        Returns 0 if no valid prices are found.

    Note:
        Scrapes data from https://www.imoti.net/bg/sredni-ceni
        Processes only numeric values, skipping any non-numeric entries.
    """
    try:
        url = "https://www.imoti.net/bg/sredni-ceni"
        response = requests.get(url, timeout=30)
        soup = BeautifulSoup(response.content, "html.parser")
        price_per_sqm_rows = soup.find("tbody").find_all("tr")

        total_price = 0
        count = 0

        for row in price_per_sqm_rows:
            cells = row.find_all("td")
            if len(cells) > 1:
                price_cell = cells[1].get_text(strip=True).replace(" ", "")
                try:
                    price = float(price_cell)
                    total_price += price
                    count += 1
                except ValueError:
                    continue

        if count > 0:
            return total_price / count
        return None
    except Exception as e:
        print(f"Error fetching SQM price: {e}")
        return None


def get_btc_price_in_eur() -> float:
    """
    Fetches the current Bitcoin price in EUR using CoinDesk API and currency conversion.

    Returns:
        float: Current Bitcoin price in EUR.

    Note:
        Uses CoinDesk API for BTC/USD price
        Uses exchangerate-api.com for USD/EUR conversion
    """
    try:
        btc_url = "https://api.coindesk.com/v1/bpi/currentprice/BTC.json"
        exchange_rate_url = "https://api.exchangerate-api.com/v4/latest/USD"

        btc_response = requests.get(btc_url, timeout=30).json()
        btc_price_usd = float(btc_response["bpi"]["USD"]["rate"].replace(",", ""))

        exchange_rate_response = requests.get(exchange_rate_url, timeout=5).json()
        usd_to_eur_rate = exchange_rate_response["rates"]["EUR"]

        return btc_price_usd * usd_to_eur_rate
    except Exception as e:
        print(f"Error fetching BTC price: {e}")
        return None


def get_prices_and_ratio() -> None:
    try:
        conn = db.connect("sql_vs_btc.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                btc_price REAL NOT NULL,
                sqm_price REAL NOT NULL,
                ratio REAL NOT NULL
            )
            """
        )

        today = datetime.now().strftime("%d %b %Y")
        cursor.execute("SELECT 1 FROM data WHERE date = ?", (today,))
        if cursor.fetchone():
            logging.info(f"Entry for {today} already exists. Skipping.")
            return

        sqm_price = get_sqm_price_in_eur()
        btc_price = get_btc_price_in_eur()

        if sqm_price is None or btc_price is None:
            logging.error("Failed to fetch data. Skipping database insertion.")
            return

        ratio = sqm_price / btc_price

        cursor.execute(
            """
            INSERT OR IGNORE INTO data (date, btc_price, sqm_price, ratio)
            VALUES(?, ?, ?, ?)
            """,
            (today, btc_price, sqm_price, ratio),
        )
        logging.info(f"Added new entry for {today}")

        conn.commit()
    except db.Error as e:
        logging.error(f"Database error: {e}")
    finally:
        conn.close()

get_prices_and_ratio()
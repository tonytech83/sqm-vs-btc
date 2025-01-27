import logging
import os
from datetime import datetime
from typing import List, Dict

import psycopg2 as db
from psycopg2.extras import RealDictCursor
import requests
from bs4 import BeautifulSoup


def prepare_json() -> List[Dict]:
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
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT * FROM data")
        # Fetch rows as dictionaries
        db_entries = cursor.fetchall()

        # Debugging: Log the number of entries fetched
        logging.info(f"Fetched {len(db_entries)} entries from the database.")

        return db_entries
    except db.Error as e:
        logging.error(f"Database error: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()


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
            """
        )

        today = datetime.now().strftime("%d %b %Y")
        cursor.execute("SELECT 1 FROM data WHERE date = %s", (today,))
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
            INSERT INTO data (date, btc_price, sqm_price, ratio)
            VALUES(%s, %s, %s, %s)
            ON CONFLICT (date) DO NOTHING
            """,
            (today, btc_price, sqm_price, ratio),
        )
        logging.info(f"Added new entry for {today}")

        conn.commit()
    except db.Error as e:
        logging.error(f"Database error: {e}")
    finally:
        if conn is not None:
            conn.close()


get_prices_and_ratio()

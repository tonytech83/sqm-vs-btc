import logging
import os
from datetime import datetime
from typing import List, Dict

import psycopg2 as db
from psycopg2.extras import RealDictCursor
import requests
from bs4 import BeautifulSoup


def prepare_json() -> List[Dict]:
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

def get_latest_prices() -> Dict:
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
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM data ORDER BY id DESC LIMIT 1")
        latest_entry = cursor.fetchone()
        
        return latest_entry
    except db.Error as e:
        logging.error(f"Database error: {e}")
        return None
    finally:
        if conn is not None:
            conn.close()


def get_sqm_price_in_eur() -> float:
    """
    Scrapes the average square meter price in EUR from imoti.net for properties in Sofia.
    Uses a list of proxies and tries each one until successful.
    """
    proxies_list = [
        {'http': 'http://45.58.252.244:3128', 'https': 'https://45.58.252.244:3128'},
        {'http': 'http://157.97.105.191:3128', 'https': 'https://157.97.105.191:3128'},
        {'http': 'http://209.126.4.70:3128', 'https': 'https://209.126.4.70:3128'},
        {'http': 'http://168.228.44.66:3128', 'https': 'https://168.228.44.66:3128'},
        {'http': 'http://159.89.239.166:3128', 'https': 'https://159.89.239.166:3128'},
        {'http': 'http://63.143.57.119:3128', 'https': 'https://63.143.57.119:3128'},
        {'http': 'http://152.26.229.52:3128', 'https': 'https://152.26.229.52:3128'},
    ]

    url = "https://www.imoti.net/bg/sredni-ceni"
    
    for proxy in proxies_list:
        try:
            logging.info(f"Trying proxy: {proxy['http']}")
            response = requests.get(url, timeout=60, proxies=proxy)
            response.raise_for_status()
            
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
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Error with proxy {proxy['http']}: {e}")
            continue
    
    logging.error("All proxies failed to fetch SQM price")
    return None

def get_btc_price_coingecko():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["bitcoin"]["eur"]
    except requests.RequestException as e:
        logging.error(f"Error fetching BTC price from CoinGecko: {e}")
        return None

def get_btc_price_binance():
    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCEUR"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data["price"])
    except requests.RequestException as e:
        logging.error(f"Error fetching BTC price from Binance: {e}")
        return None

def get_btc_price_kraken():
    url = "https://api.kraken.com/0/public/Ticker?pair=XBTEUR"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data["result"]["XXBTZEUR"]["c"][0])
    except requests.RequestException as e:
        logging.error(f"Error fetching BTC price from Kraken: {e}")
        return None

def get_btc_price_in_eur() -> float:
    for source in [get_btc_price_coingecko, get_btc_price_binance, get_btc_price_kraken]:
        price = source()
        if price:
            logging.info(f"BTC Price from {source.__name__}: {price} EUR")
            return price
    logging.error("Failed to fetch BTC price from all sources.")
    return None


def get_prices_and_ratio() -> None:
    """
    Fetches current BTC and square meter prices, calculates their ratio,
    and stores the data in the database.

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

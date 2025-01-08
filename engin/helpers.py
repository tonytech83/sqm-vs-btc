import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime


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
    url = "https://www.imoti.net/bg/sredni-ceni"
    response = requests.get(url)
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
        average_price = total_price / count
    else:
        average_price = 0

    return average_price


def get_btc_price_in_eur() -> float:
    """
    Fetches the current Bitcoin price in EUR using CoinDesk API and currency conversion.
    
    Returns:
        float: Current Bitcoin price in EUR.
    
    Note:
        Uses CoinDesk API for BTC/USD price
        Uses exchangerate-api.com for USD/EUR conversion
    """
    btc_url = "https://api.coindesk.com/v1/bpi/currentprice/BTC.json"
    exchange_rate_url = "https://api.exchangerate-api.com/v4/latest/USD"

    # Get Bitcoin price in USD
    btc_response = requests.get(btc_url).json()
    btc_price_usd = float(btc_response["bpi"]["USD"]["rate"].replace(",", ""))

    # Get USD to EUR conversion rate
    exchange_rate_response = requests.get(exchange_rate_url).json()
    usd_to_eur_rate = exchange_rate_response["rates"]["EUR"]

    # Convert USD price to EUR
    return btc_price_usd * usd_to_eur_rate


def write_json_data(file_path: str, new_entry: dict) -> None:
    """
    Atomically writes a new entry to a JSON file, maintaining one entry per line.
    
    Args:
        file_path (str): Path to the JSON file
        new_entry (dict): New data entry to append to the file
    
    Note:
        Uses a temporary file for atomic writing
        Maintains file format with one JSON object per line
    """
    temp_file = file_path + ".tmp"

    # Append new entry atomically
    with open(file_path, "r") as f:
        data = [json.loads(line) for line in f if line.strip()]

    data.append(new_entry)

    # Write to a temporary file first
    with open(temp_file, "w") as f:
        for entry in data:
            json.dump(entry, f)
            f.write("\n")

    # Replace the original file
    os.replace(temp_file, file_path)


def get_prices_and_ratio() -> None:
    """
    Fetches current BTC and square meter prices, calculates their ratio, and stores the data.
    
    The function:
    - Creates data directory and file if they don't exist
    - Checks for existing entry for current date to avoid duplicates
    - Fetches current BTC and square meter prices
    - Calculates the ratio between them
    - Stores the data in JSON format
    
    Data stored includes:
    - date: Current UTC date
    - btc_price: Bitcoin price in EUR
    - sqm_price: Square meter price in EUR
    - ratio: SQM price / BTC price
    
    Note:
        Stores data in 'data/data.json'
        Skips execution if an entry for current date exists
    """
    file_path = "data/data.json"

    # Ensure the data directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Ensure the file exists
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            pass  # Create an empty file

    # Read existing data
    existing_data = []
    if os.path.getsize(file_path) > 0:
        with open(file_path, "r") as json_file:
            existing_data = [json.loads(line) for line in json_file if line.strip()]

    # Check if today's data already exists
    today = datetime.utcnow().strftime("%d %b %Y")
    if any(entry["date"] == today for entry in existing_data):
        print(f"Entry for {today} already exists. Skipping.")
        return

    # Fetch new data
    sqm_price = get_sqm_price_in_eur()
    btc_price = get_btc_price_in_eur()
    ratio = sqm_price / btc_price

    new_entry = {
        "date": today,
        "btc_price": btc_price,
        "sqm_price": sqm_price,
        "ratio": ratio,
    }

    # Append new data to the file atomically
    write_json_data(file_path, new_entry)
    print(f"Added new entry for {today}: {new_entry}")

import os
from flask import Flask, render_template, jsonify
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

app = Flask(__name__)

# Configure static file serving
app.static_folder = "static"
app._static_url_path = "./static"


def get_sqm_price_in_eur():
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


def get_btc_price_in_eur():
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


def write_json_data(file_path, data):
    with open(file_path, "a") as file:
        json.dump(data, file)
        file.write("\n")


def get_prices_and_ratio():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists("data/data.json"):
        with open("data/data.json", "w") as f:
            pass

    data = []
    if os.path.getsize("data/data.json") > 0:
        with open("data/data.json", "r") as json_file:
            data = [json.loads(line) for line in json_file if line.strip()]

    now = datetime.utcnow()
    if data:
        last_entry = data[-1]
        last_entry_time = datetime.strptime(last_entry["date"], "%d %b %Y")
        if (now - last_entry_time).total_seconds() < 86400:
            return

    sqm_price = get_sqm_price_in_eur()
    btc_price = get_btc_price_in_eur()
    ratio = sqm_price / btc_price
    dict_data = {
        "date": now.strftime("%d %b %Y"),
        "btc_price": btc_price,
        "sqm_price": sqm_price,
        "ratio": ratio,
    }
    write_json_data("data/data.json", dict_data)


@app.route("/data")
def data():
    get_prices_and_ratio()

    with open("data/data.json", "r") as json_file:
        data = [json.loads(line) for line in json_file if line.strip()]

    return jsonify(data)


@app.route("/")
def index():
    date = datetime.now().strftime("%d %b %Y")
    btc_price = f"{get_btc_price_in_eur():.2f}"
    sqm_price = f"{get_sqm_price_in_eur():.2f}"
    return render_template(
        "index.html", date=date, btc_price=btc_price, sqm_price=sqm_price
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port)

from flask import Flask, render_template, jsonify
import requests
from bs4 import BeautifulSoup
from datetime import datetime

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


def get_ratio():
    apt_price = get_sqm_price_in_eur()
    btc_price = get_btc_price_in_eur()
    ratio = apt_price / btc_price
    return {
        "date": datetime.now().strftime("%d-%m-%Y"),
        "ratio": ratio,
    }


@app.route("/data")
def data():
    ratio = get_ratio()
    return jsonify(ratio)


@app.route("/")
def index():
    date = datetime.now().strftime("%d-%m-%Y")
    current_price = f"{get_btc_price_in_eur():.2f}"
    return render_template("index.html", date=date, current_price=current_price)


if __name__ == "__main__":
    app.run(debug=True)

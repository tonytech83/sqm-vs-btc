import os
from flask import Flask, render_template, jsonify
from datetime import datetime
import json

from engin.helpers import get_sqm_price_in_eur, get_btc_price_in_eur, get_prices_and_ratio


app = Flask(
    __name__,
    static_url_path="/static",
    static_folder="static",
    template_folder="templates",
)


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

import os
from flask import Flask, render_template, jsonify
from functools import lru_cache
from datetime import datetime

from engin.helpers import get_sqm_price_in_eur, get_btc_price_in_eur, get_prices_and_ratio, prepare_json


app = Flask(
    __name__,
    static_url_path="/static",
    static_folder="static",
    template_folder="templates",
)

current_btc_price = None
current_sqm_price = None
data_preloaded = False

@app.before_request
def preload_data():
    global current_btc_price, current_sqm_price, data_preloaded
    if not data_preloaded:
        current_btc_price = f"{get_btc_price_in_eur():.2f}"
        current_sqm_price = f"{get_sqm_price_in_eur():.2f}"
        data_preloaded = True

# Cache results for /data
@lru_cache(maxsize=1)  
def cached_data():
    return prepare_json()


@app.route("/data")
def data():
    get_prices_and_ratio()
    return jsonify(cached_data())


@app.route("/")
def index():
    date = datetime.now().strftime("%d %b %Y")
    return render_template(
        "index.html", date=date, btc_price=current_btc_price, sqm_price=current_sqm_price
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port)

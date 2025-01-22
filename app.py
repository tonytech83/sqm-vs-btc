import os
from flask import Flask, render_template, jsonify, g
from functools import lru_cache
from datetime import datetime

from engin.helpers import prepare_json
from engin.insert_into_db import (
    get_sqm_price_in_eur,
    get_btc_price_in_eur,
    get_prices_and_ratio,
)


@lru_cache(maxsize=1)
def cached_data():
    return prepare_json()


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_url_path="/static",
        static_folder="static",
        template_folder="templates",
    )

    @app.before_request
    def preload_data():
        if not hasattr(g, "data_preloaded"):
            g.current_btc_price = f"{get_btc_price_in_eur():.2f}"
            g.current_sqm_price = f"{get_sqm_price_in_eur():.2f}"
            g.data_preloaded = True

    @app.route("/data")
    def data():
        return jsonify(cached_data())

    @app.route("/update-db")
    def update_db():
        get_prices_and_ratio()
        return jsonify({"status": "Database updated"})

    @app.route("/")
    def index():
        date = datetime.now().strftime("%d %b %Y")
        return render_template(
            "index.html",
            date=date,
            btc_price=g.current_btc_price,
            sqm_price=g.current_sqm_price,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port)

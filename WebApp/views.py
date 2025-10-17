from datetime import datetime
from functools import lru_cache
from typing import ClassVar

from flask import jsonify, render_template
from flask.views import View

from WebApp.helpers import get_latest_prices, get_prices_and_ratio, prepare_json


@lru_cache(maxsize=1)
def cached_data():
    return prepare_json()


class IndexView(View):
    methods: ClassVar[list[str]] = ["GET"]

    def __init__(self, template):
        self.template = template

    def dispatch_request(self):
        latest_data = get_latest_prices()

        if latest_data:
            return render_template(
                self.template,
                date=latest_data["date"],
                btc_price=f"{float(latest_data['btc_price']):.2f}",
                sqm_price=f"{float(latest_data['sqm_price']):.2f}",
            )
        return render_template(
            self.template,
            date=datetime.now(tz=datetime.UTC).strftime("%d %b %Y"),
            btc_price=None,
            sqm_price=None,
        )


class DataView(View):
    methods: ClassVar[list[str]] = ["GET"]

    def dispatch_request(self):
        return jsonify(cached_data())


class UpdateDBView(View):
    methods: ClassVar[list[str]] = ["GET"]

    def dispatch_request(self):
        get_prices_and_ratio()

        return jsonify({"status": "Database updated"})

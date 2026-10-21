from datetime import datetime, timezone
from typing import ClassVar

from flask import jsonify, render_template
from flask.views import View
from flask.wrappers import Response

from WebApp.helpers import get_latest_prices, get_prices_and_ratio, prepare_json


class IndexView(View):
    methods: ClassVar[list[str]] = ["GET"]

    def __init__(self, template) -> None:
        self.template = template

    def dispatch_request(self) -> str:
        latest_data = get_latest_prices()

        if latest_data:
            btc_price = float(latest_data["btc_price"])
            sqm_price = float(latest_data["sqm_price"])
            return render_template(
                self.template,
                date=latest_data["date"],
                btc_price=f"{btc_price:.2f}",
                sqm_price=f"{sqm_price:.2f}",
                ratio=f"{float(latest_data['ratio']):.6f}",
                sqm_per_btc=f"{btc_price / sqm_price:.2f}",
            )
        return render_template(
            self.template,
            date=datetime.now(tz=timezone.utc).strftime("%Y-%m-%d"),
            btc_price=None,
            sqm_price=None,
            ratio=None,
            sqm_per_btc=None,
        )


class DataView(View):
    methods: ClassVar[list[str]] = ["GET"]

    def dispatch_request(self) -> Response:
        return jsonify(prepare_json())


class UpdateDBView(View):
    methods: ClassVar[list[str]] = ["GET"]

    def dispatch_request(self) -> tuple[Response, int]:
        result = get_prices_and_ratio()
        status_code = 500 if result == "failed" else 200

        return jsonify({"status": result}), status_code

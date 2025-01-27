from datetime import datetime
from functools import lru_cache

from flask import render_template, jsonify, g
from flask.views import View


from WebApp.helpers import prepare_json
from WebApp.helpers import get_prices_and_ratio


@lru_cache(maxsize=1)
def cached_data():
    return prepare_json()


class IndexView(View):
    methods = ["GET"]

    def __init__(self, template):
        self.template = template

    def dispatch_request(self):
        date = datetime.now().strftime("%d %b %Y")
        return render_template(
            self.template,
            date=date,
            btc_price=g.current_btc_price,
            sqm_price=g.current_sqm_price,
        )


class DataView(View):
    methods = ["GET"]

    def dispatch_request(self):

        return jsonify(cached_data())


class UpdateDBView(View):
    methods = ["GET"]

    def dispatch_request(self):
        get_prices_and_ratio()

        return jsonify({"status": "Database updated"})

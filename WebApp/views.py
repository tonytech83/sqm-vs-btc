from datetime import datetime
from functools import lru_cache

from flask import render_template, jsonify
from flask.views import View


from WebApp.helpers import prepare_json, get_prices_and_ratio, get_latest_prices



@lru_cache(maxsize=1)
def cached_data():
    return prepare_json()


class IndexView(View):
    methods = ["GET"]

    def __init__(self, template):
        self.template = template

    def dispatch_request(self):
        latest_data = get_latest_prices()

        if latest_data:
            return render_template(
                self.template,
                date=latest_data['date'],
                btc_price=latest_data['btc_price'],
                sqm_price=latest_data['sqm_price'],
            )
        return render_template(
            self.template,
            date=datetime.now().strftime("%d %b %Y"),
            btc_price=None,
            sqm_price=None,
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

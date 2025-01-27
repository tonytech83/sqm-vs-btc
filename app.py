import os
from flask import Flask, g

from WebApp.helpers import get_sqm_price_in_eur, get_btc_price_in_eur
from WebApp.views import IndexView, DataView, UpdateDBView


# Initialise Flask App
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


# urlpatterns
app.add_url_rule("/", view_func=IndexView.as_view("index_view", "index.html"))
app.add_url_rule("/data", view_func=DataView.as_view("data_view"))
app.add_url_rule("/update-db", view_func=UpdateDBView.as_view("update_db_view"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port)

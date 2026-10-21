import os

from flask import Flask

from WebApp.views import DataView, IndexView, UpdateDBView

# Initialise Flask App
app = Flask(
    __name__,
    static_url_path="/static",
    static_folder="static",
    template_folder="templates",
)


# urlpatterns
app.add_url_rule("/", view_func=IndexView.as_view("index_view", "index.html"))
app.add_url_rule("/data", view_func=DataView.as_view("data_view"))
app.add_url_rule("/update-db", view_func=UpdateDBView.as_view("update_db_view"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port)

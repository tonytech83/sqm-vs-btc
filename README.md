[![Build and Deploy](https://github.com/tonytech83/sqm-vs-btc/actions/workflows/main.yml/badge.svg)](https://github.com/tonytech83/sqm-vs-btc/actions/workflows/main.yml)
[![Schedule for GET requests](https://github.com/tonytech83/sqm-vs-btc/actions/workflows/keep_it_alive.yml/badge.svg)](https://github.com/tonytech83/sqm-vs-btc/actions/workflows/keep_it_alive.yml)

# SQM vs BTC

A Flask-based web application that compares the average price per square meter of real estate in Sofia with the current price of Bitcoin (BTC). The app dynamically fetches real estate prices and Bitcoin prices, calculates their ratio, and provides visual insights using Chart.js.

<div align="center" display="flex">
    <img src="./pic.jpg" alt="app">
</div>

---

## Features

- Web Interface: Displays the latest data for sqm and BTC prices along with their ratio.
  - Real estate prices are scraped from [Imoti.net](https://www.imoti.net/bg/sredni-ceni).
  - Bitcoin prices are fetched from the [Coindesk API](https://www.coindesk.com/coindesk-api).
- Data Caching: Cached results for efficient API response.
- SQLite Integration: Stores daily sqm and BTC prices with a unique entry per day.
- Error Handling: Ensures no invalid data is stored in the database if fetching fails.
- Preloading Data: Preloads sqm and BTC prices during the first request to optimize user experience.

---

## Project Structure

```plain
sqm-vs-btc/
├── engin/
│   └── helpers.py      # Helper functions for data fetching and database operations
├── static/             # Static files (CSS, JS, etc.)
│   ├── chart.js
│   └── styles.css
├── templates/
│   └── index.html      # HTML template for the web interface
├── app.py              # Flask application entry point
├── Dockerfile
├── pic.jpg
├── README.md           # Project documentation
├── requirements.txt    # Python dependencies
└── sql_vs_btc.db       # SQLite database
```

## Requirements
- Python 3.8+
- Flask
- BeautifulSoup (bs4)
- Requests
- SQLite3

## Installation
1. Clone the repository:
```sh
git clone https://github.com/tonytech83/sqm-vs-btc.git
cd sqm-vs-btc
```
2. Create and activate a virtual environment:
```sh
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install dependencies:
```sh
pip install -r requirements.txt
```
## Running the Application
1. Start the application:
```sh
flask run # or python app.py
```
2. Open the application in your browser at http://127.0.0.1:5000.

## Database Schema
```sql
CREATE TABLE IF NOT EXISTS data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    btc_price REAL NOT NULL,
    sqm_price REAL NOT NULL,
    ratio REAL NOT NULL
);
```

## License

This project is open-source and available under the MIT License.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

<br/>

<h6 align="center"> Made with by Anton Petrov </h6>

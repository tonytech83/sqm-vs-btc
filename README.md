[![Build and Deploy](https://github.com/tonytech83/sqm-vs-btc/actions/workflows/main.yml/badge.svg)](https://github.com/tonytech83/sqm-vs-btc/actions/workflows/main.yml)
[![Schedule for GET requests](https://github.com/tonytech83/sqm-vs-btc/actions/workflows/keep_it_alive.yml/badge.svg)](https://github.com/tonytech83/sqm-vs-btc/actions/workflows/keep_it_alive.yml)

# Square Meter vs. Bitcoin

A Flask-based web application that compares the average price per square meter of real estate in Sofia with the current price of Bitcoin (BTC). The app dynamically fetches real estate prices and Bitcoin prices, calculates their ratio, and provides visual insights using Chart.js.

---

## Features

- **Dynamic Data Fetching**:
  - Real estate prices are scraped from [Imoti.net](https://www.imoti.net/bg/sredni-ceni).
  - Bitcoin prices are fetched from the [Coindesk API](https://www.coindesk.com/coindesk-api).

- **REST API**:
  - `/data`: Returns the ratio of one square meter price to the Bitcoin price as a JSON response.

- **Frontend Rendering**:
  - Uses Flask templates to display the current price of Bitcoin and the calculated ratio.
  - Visualizes data with Chart.js for interactive charts.

---

## Project Structure

```plain
sqm-vs-btc/
├── app.py                # Main application file
├── Dockerfile
├── README.md             # Documentation for the project
├── requirements.txt      # List of Python dependencies
├── static/
│   └── styles.css        # Custom styles
└── templates/
    └── index.html        # HTML template for the web app
```

## Installation and Setup
### Prerequisites
- Python 3.10 or later
- pip (Python package manager)

### Installation
1. Clone the repository:
```sh
git clone https://github.com/tonytech83/sqm-vs-btc.git
cd one-square-meter-vs-btc
```
2. Create and activate a virtual environment:
```sh
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```
3. Install dependencies:
```sh
pip install -r requirements.txt
```
### Running the Application
1. Set the Flask environment variable:
```sh
export FLASK_APP=app.py
export FLASK_ENV=development  # For development mode
```
2. Start the application:
```sh
flask run
```
3. Open the application in your browser at http://127.0.0.1:5000.

<br/>
<br/>

<h6 align="center"> Made with by Anton Petrov </h6>

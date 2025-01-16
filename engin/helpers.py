import sqlite3 as db


def prepare_json():
    conn = db.connect("sql_vs_btc.db")
    conn.row_factory = db.Row  # Fetch rows as dictionaries
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM data")
    # Convert rows to dictionaries
    db_entries = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return db_entries

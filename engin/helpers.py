import sqlite3 as db
from typing import List, Dict


def prepare_json() -> List[Dict]:
    try:
        conn = db.connect("sql_vs_btc.db")
        conn.row_factory = db.Row  # Fetch rows as dictionaries
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM data")
        # Convert rows to dictionaries
        db_entries = [dict(row) for row in cursor.fetchall()]

        return db_entries
    except db.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

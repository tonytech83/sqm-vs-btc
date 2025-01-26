import psycopg2 as db
from psycopg2.extras import RealDictCursor
from typing import List, Dict
import logging
import os


def prepare_json() -> List[Dict]:
    # Initialize conn to None
    conn = None  
    try:
        conn = db.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        # Use RealDictCursor for dict rows
        cursor = conn.cursor(cursor_factory=RealDictCursor)  

        cursor.execute("SELECT * FROM data")
        # Fetch rows as dictionaries
        db_entries = cursor.fetchall()

        # Debugging: Log the number of entries fetched
        logging.info(f"Fetched {len(db_entries)} entries from the database.")

        return db_entries
    except db.Error as e:
        logging.error(f"Database error: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()

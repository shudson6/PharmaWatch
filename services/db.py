import os

from dotenv import load_dotenv
import psycopg2

load_dotenv()

def get_connection_info() -> dict:
    return {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }

def get_connection() -> psycopg2.extensions.connection:
    return psycopg2.connect(**get_connection_info())

def get_watch_list():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT symbol FROM investing.watchlist
        WHERE active;
    """)
    watchlist = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return watchlist

def save_new_article(symbol, date, title, content_type, content, url, retrieved_ts):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO investing.press_release
        (symbol, date, title, content_type, content, url, retrieved_ts)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """, (symbol, date, title, content_type, content, url, retrieved_ts))
    pr_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    return pr_id

"""Collection of functions to write to and read from the database."""
import os

import psycopg2

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

def get_titles_for_symbol(symbol: str):
    """Get a list of (title, date) tuples for the given symbol."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, date
        FROM investing.press_release
        WHERE symbol = %s;
    """, (symbol,))
    titles = [(row[0], row[1]) for row in cursor.fetchall()]
    cursor.close()
    return titles

def get_watch_list():
    """Get the list of symbols being actively monitored."""
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
    """Save an article to the database. Return the new article's ID.

    Args:
        symbol (str): the associated stock symbol
        date (datetime.date or str): the publication date of the article
        title (str): the title of the article
        content_type (str): the MIME type of the content being stored
        content (str): the content of the article
        url (str): the URL where the article was retrieved
        retrieved_ts (datetime): datetime when the article was retrieved

    Returns:
        str: ID of the new article record
    """
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

def save_new_article_summary(pr_id, category, sentiment, summary, timestamp, model, prompt):
    """Save a summary for an article to the database.

    Args:
        pr_id (str): ID of the article being summarized
        summary (str): the summary text
        timestamp (datetime): when the summary was created
        model (str): name of the model used to summarize the article
        prompt (json): the prompt used to generate the summary, preferably not
            including the article content (use a placeholder instead)

    Returns:
        str: ID of the new summary record
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO investing.pr_summary
        (pr_id, category, sentiment, summary, timestamp, model_used, prompt)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """, (pr_id, category, sentiment, summary, timestamp, model, prompt))
    summary_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    return summary_id

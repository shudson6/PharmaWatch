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

def get_article(id_or_symbol: (str | int), title: str=None):
    """Retrieve a news article from the database.

    Args:
        id_or_symbol (str, optional): the article ID or symbol. if title is provided,
        this is the symbol, otherwise it is assumed to be the article ID.
        title (str, optional): the title of the article

    Returns:
        dict: article data, or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    if title is None:
        cursor.execute("""
            SELECT id, symbol, date, title, content_type, content, url, retrieved_ts
            FROM investing.press_release
            WHERE id = %s;
        """, (id_or_symbol,))
    else:
        cursor.execute("""
            SELECT id, symbol, date, title, content_type, content, url, retrieved_ts
            FROM investing.press_release
            WHERE symbol = %s AND title = %s;
        """, (id_or_symbol, title))
    row = cursor.fetchone()
    cursor.close()
    if row:
        return {
            "pr_id": row[0],
            "symbol": row[1],
            "date": row[2],
            "title": row[3],
            "content_type": row[4],
            "content": row[5],
            "document_url": row[6],
            "retrieved_ts": row[7],
        }
    return None

def get_article_with_summary(id_or_symbol: (str | int), title: str=None):
    """Retrieve a news article and its summary from the database.

    Args:
        id_or_symbol (str, optional): the article ID or symbol. if title is provided,
        this is the symbol, otherwise it is assumed to be the article ID.
        title (str, optional): the title of the article

    Returns:
        dict: article data with summary, or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    if title is None:
        cursor.execute("""
            SELECT pr.id, pr.symbol, pr.date, pr.title, pr.content_type,
                   pr.content, pr.url, pr.retrieved_ts,
                   ps.id, ps.category, ps.sentiment, ps.summary,
                   ps.timestamp, ps.model_used, ps.prompt
            FROM investing.press_release pr
            LEFT JOIN investing.pr_summary ps ON pr.id = ps.pr_id
            WHERE pr.id = %s;
            ORDER BY ps.timestamp DESC LIMIT 1;
        """, (id_or_symbol,))
    else:
        cursor.execute("""
            SELECT pr.id, pr.symbol, pr.date, pr.title, pr.content_type,
                   pr.content, pr.url, pr.retrieved_ts,
                   ps.id, ps.category, ps.sentiment, ps.summary,
                   ps.timestamp, ps.model_used, ps.prompt
            FROM investing.press_release pr
            LEFT JOIN investing.pr_summary ps ON pr.id = ps.pr_id
            WHERE pr.symbol = %s AND pr.title = %s
            ORDER BY ps.timestamp DESC LIMIT 1;
        """, (id_or_symbol, title))
    row = cursor.fetchone()
    cursor.close()
    if row:
        return {
            "pr_id": row[0],
            "symbol": row[1],
            "date": row[2],
            "title": row[3],
            "content_type": row[4],
            "content": row[5],
            "document_url": row[6],
            "retrieved_ts": row[7],
            "summary_id": row[8],
            "category": row[9],
            "sentiment": row[10],
            "summary": row[11],
            "timestamp": row[12],
            "model_used": row[13],
            "prompt": row[14],
        }
    return None

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

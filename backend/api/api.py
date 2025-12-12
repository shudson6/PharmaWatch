import logging

from flask import Flask, request

from services import db, StockDataService

logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/api/articles/<symbol>", methods=["GET"])
def get_articles(symbol: str):
    """API endpoint to get articles for a given stock symbol.

    Args:
        symbol (str): Stock symbol to retrieve articles for.
    """
    logger.info(f"Received request for articles for symbol: {symbol}")
    titles = db.get_titles_for_symbol(symbol.upper())
    articles = [
        db.get_article_with_summary(symbol.upper(), title)
        for title, _ in titles
    ]
    logger.info(f"Returning {len(articles)} articles for symbol: {symbol}")
    return articles

@app.route("/api/price-history/<symbol>", methods=["GET"])
def get_price_history(symbol: str):
    """API endpoint to get price history for a given stock symbol.

    Args:
        symbol (str): Stock symbol to retrieve price history for.
    """
    logger.info(f"Received request for price history for symbol: {symbol}")
    price_history = StockDataService.fetch_price_history(symbol.upper())
    logger.info(f"Returning {len(price_history)} price history records for symbol: {symbol}")
    return [{
        "Date": idx.strftime("%Y-%m-%d"),
        "Close": price_history[symbol.upper()]["Close"][idx],
    } for idx in price_history[symbol.upper()].index]
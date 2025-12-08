import logging

import yfinance as yf

logger = logging.getLogger(__name__)

def fetch_price_history(symbol: (str | list | tuple)):
    logger.info(f"Fetching price history for {symbol}")
    data = yf.download(symbol, period="1y", group_by="ticker", interval="1d",
                       auto_adjust=True)
    logger.info(f"Fetched {len(data)} days price data for {symbol}")
    return data

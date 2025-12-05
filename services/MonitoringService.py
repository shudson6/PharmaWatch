import importlib
import logging

from monitors import MonitorBase
from services import db, SummarizationService

logger = logging.getLogger(__name__)

def resolve_monitor_name(symbol: str):
    return (
        f"monitors.{symbol.lower()}",
        f"{symbol.capitalize()}Monitor"
    )

def start():
    logger.info("Starting Monitoring Service")
    watchlist = db.get_watch_list()
    logger.debug(f"Found {len(watchlist)} watches: {watchlist}")
    for symbol in watchlist:
        logger.debug(f"Monitor for {symbol}: {resolve_monitor_name(symbol)}")
        module_name, class_name = resolve_monitor_name(symbol)
        monitor: MonitorBase
        monitor = getattr(importlib.import_module(module_name), class_name)()
        new_articles = monitor.fetch_news_articles()
        logger.info(f"Found {len(new_articles)} new articles for {symbol}")
        for a in new_articles:
            try:
                a['pr_id'] = db.save_new_article(
                    symbol, a['date'], a['title'], a['content-type'],
                    a['content'], a['document_url'], a['retrieved_ts']
                )
            except Exception as e:
                logger.warning(f"{type(e).__name__} occurred while saving"
                               f"article {a['title']}. Article not saved")
        for a in new_articles:
            if "pr_id" in a:
                SummarizationService.queue_article(a)
    logger.info("MonitoringService finished.")

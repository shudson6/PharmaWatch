import importlib
import logging
import os
import time

from monitors import MonitorBase
from services import db, NewsAnalysisService

logger = logging.getLogger(__name__)

def resolve_monitor_name(symbol: str):
    return (
        f"monitors.{symbol.lower()}",
        f"{symbol.capitalize()}Monitor"
    )

def start():
    logger.info("Starting Monitoring Service")
    while True:
        start_time = int(round(time.time(), 0))
        monitors_executed = 0
        articles_found = 0
        missing_monitors = []
        articles_not_saved = 0
        other_errors = []
        watchlist = db.get_watch_list()
        logger.debug(f"Found {len(watchlist)} watches: {watchlist}")
        driver = MonitorBase('').start_web_driver(headless=True)
        for symbol in watchlist:
            module_name, class_name = resolve_monitor_name(symbol)
            logger.debug(f"Monitor for {symbol}: {module_name}.{class_name}")
            monitor: MonitorBase
            try:
                monitor = getattr(importlib.import_module(module_name), class_name)()
            except (ModuleNotFoundError, AttributeError) as e:
                logger.error(f"Failed to load monitor for {symbol}: "
                             f"{type(e).__name__} raised on import of "
                             f"{module_name}.{class_name}")
                missing_monitors.append((symbol, class_name))
                continue
            try:
                new_articles = monitor.fetch_news_articles(driver)
                logger.info(f"Found {len(new_articles)} new articles for {symbol}")
                articles_found += len(new_articles)
                for a in new_articles:
                    try:
                        a['pr_id'] = db.save_new_article(
                            symbol, a['date'], a['title'], a['content-type'],
                            a['content'], a['document_url'], a['retrieved_ts']
                        )
                    except Exception as e:
                        logger.error(f"{type(e).__name__} occurred while saving"
                                    f"article {a['title']}. Article not saved")
                        articles_not_saved += 1
                for a in new_articles:
                    if "pr_id" in a:
                        NewsAnalysisService.queue_article(a)
                monitors_executed += 1
            except Exception as e:
                logger.error(f"Unexpected {type(e).__name__} occurred while "
                             f"monitoring {symbol} news: {e}")
                other_errors.append((symbol, type(e).__name__))
            # get rid of it so maybe it get's garbage collected
            # and thus refreshed for the next run
            del monitor
        driver.quit()
        end_time = int(round(time.time(), 0))
        elapsed = end_time - start_time
        message = (
            f"MonitoringService finished in {elapsed}s\n"
            " Monitors | Articles | Failures |  Errors  \n"
            f"{monitors_executed:^10d}|{articles_found:^10d}|"
            f"{articles_not_saved:^10d}|{len(other_errors):^10d}"
        )
        if missing_monitors:
            message += "\nMonitors not found:\n"
            message += "\n".join(
                f"{s} ({c})" for s, c in missing_monitors
            )
        if other_errors:
            message += "\nErrors:\n"
            message += "\n".join(
                f"{s}: (t)" for s, t in other_errors
            )
        if any([missing_monitors, articles_not_saved, other_errors]):
            logger.warning(message)
        else:
            logger.info(message)
        
        next_time = start_time
        while next_time < end_time:
            next_time += int(os.getenv("PASSIVE_WATCH_INTERVAL"))
        wait_time = next_time - end_time
        logger.info(f"Next run in {wait_time}s")
        time.sleep(wait_time)

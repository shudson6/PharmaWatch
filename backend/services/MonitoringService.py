import datetime
import logging
import os
import time

import yaml

from monitors import MonitorBase
from services import db, NewsAnalysisService

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "monitoring.yaml")

def load_config():
    """Load monitoring configuration from YAML file."""
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def get_monitor_config(config, symbol):
    """Get the press_releases config for a given symbol."""
    symbol_lower = symbol.lower()
    company_config = config.get("company", {}).get(symbol_lower)
    if not company_config:
        return None
    return company_config.get("press_releases")

def run_once(config=None):
    """Run a single monitoring pass for all symbols in the watchlist."""
    config = config or load_config()
    start_time = int(round(time.time(), 0))
    monitors_executed = 0
    articles_found = 0
    missing_configs = []
    articles_not_saved = 0
    other_errors = []
    watchlist = db.get_watch_list()
    logger.debug(f"Found {len(watchlist)} watches: {watchlist}")
    try:
        for symbol in watchlist:
            search_params = get_monitor_config(config, symbol)
            if not search_params:
                logger.error(f"No configuration found for {symbol} in monitoring.yaml")
                missing_configs.append(symbol)
                continue
            logger.debug(f"Monitor config for {symbol}: {search_params.get('url')}")
            monitor = MonitorBase(symbol, search_params)
            try:
                new_articles = monitor.fetch_news_articles()
                logger.info(f"Found {len(new_articles)} new articles for {symbol}")
                articles_found += len(new_articles)
                for a in new_articles:
                    try:
                        a['pr_id'] = db.save_new_article(
                            symbol, a['date'], a['title'], a.get('content-type'),
                            a.get('content'), a.get('document_url'), a.get('retrieved_ts')
                        )
                    except Exception as e:
                        logger.error(f"{type(e).__name__} occurred while saving "
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
    finally:
        ...
    end_time = int(round(time.time(), 0))
    elapsed = end_time - start_time
    message = (
        f"MonitoringService finished in {elapsed}s\n"
        " Monitors | Articles | Failures |  Errors  \n"
        f"{monitors_executed:^10d}|{articles_found:^10d}|"
        f"{articles_not_saved:^10d}|{len(other_errors):^10d}"
    )
    if missing_configs:
        message += "\nConfigs not found:\n"
        message += "\n".join(missing_configs)
    if other_errors:
        message += "\nErrors:\n"
        message += "\n".join(
            f"{s}: {t}" for s, t in other_errors
        )
    if any([missing_configs, articles_not_saved, other_errors]):
        logger.warning(message)
    else:
        logger.info(message)
    return {
        "start_time": start_time,
        "end_time": end_time,
        "elapsed": elapsed,
        "monitors_executed": monitors_executed,
        "articles_found": articles_found,
        "articles_not_saved": articles_not_saved,
        "missing_configs": missing_configs,
        "other_errors": other_errors,
    }


def run_loop(config):
    """Run the monitoring loop indefinitely."""
    while True:
        result = run_once(config)
        start_time = result["start_time"]
        end_time = result["end_time"]
        next_time = start_time
        while next_time < end_time:
            next_time += int(os.getenv("PASSIVE_WATCH_INTERVAL"))
        wait_time = next_time - end_time
        logger.info(
            "Next run in %ds at %s",
            wait_time,
            datetime.datetime.fromtimestamp(next_time).time().isoformat()
        )
        time.sleep(wait_time)


def start():
    """Start the monitoring service."""
    logger.info("Starting Monitoring Service")
    config = load_config()
    run_loop(config)

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import StrEnum
import logging
import os

from dotenv import load_dotenv

from services import MonitoringService, NewsAnalysisService

load_dotenv()

class Color(StrEnum):
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    RESET = "\033[0m"

class ColorFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%', validate=True, *, defaults=None):
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)

    def format(self, record: logging.LogRecord):
        message = super().format(record)
        color = {
            logging.DEBUG: Color.CYAN,
            logging.WARNING: Color.YELLOW,
            logging.ERROR: Color.RED,
            logging.CRITICAL: Color.MAGENTA,
        }.get(record.levelno, None)
        if color:
            return color + message + Color.RESET
        return message

def setup_logging():
    FORMAT="%(asctime)s:%(levelname)s:%(name)s:%(lineno)d: %(message)s"
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(ColorFormatter(FORMAT))
    logging.basicConfig(
        format=FORMAT,
        handlers=[stream_handler],
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    if os.getenv("LOG_TO_FILE", False):
        logger.addHandler(logging.FileHandler(
            os.path.join(os.getcwd(), "logs",
                        "pharmawatch-" + datetime.now().strftime("%Y%m%d-%H%M") + ".log"),
            encoding="utf-8",
            delay=False,
        ))

    os.makedirs(os.path.join(os.getcwd(), "logs"), exist_ok=True)
    return logger

def start():
    logger = setup_logging()
    logger.info("Starting PharmaWatch")

    logger.info("Firing up ThreadPoolExecutor and scheduling jobs")
    executor = ThreadPoolExecutor(max_workers=3)
    executor.submit(NewsAnalysisService.start)
    executor.submit(NewsAnalysisService.queue_unsummarized_articles)
    executor.submit(MonitoringService.start)

    # wait til jobs are done, which will never happen since they're infinite loops :)
    executor.shutdown(wait=True)

if __name__ == "__main__":
    start()

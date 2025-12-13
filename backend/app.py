from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import logging
import os

from dotenv import load_dotenv

from services import MonitoringService, NewsAnalysisService

file_handler = logging.FileHandler(
    os.path.join(os.getcwd(), "logs",
                 "pharmawatch-" + datetime.now().strftime("%Y%m%d-%H%M") + ".log"),
    encoding="utf-8",
    delay=True,
)
stream_handler = logging.StreamHandler()
logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(lineno)d: %(message)s",
    handlers=[file_handler, stream_handler],
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

os.makedirs(os.path.join(os.getcwd(), "logs"), exist_ok=True)

logger.info("Starting PharmaWatch")
load_dotenv()

logger.info("Firing up ThreadPoolExecutor and scheduling jobs")
executor = ThreadPoolExecutor(max_workers=3)
executor.submit(NewsAnalysisService.start)
executor.submit(NewsAnalysisService.queue_unsummarized_articles)
executor.submit(MonitoringService.start)

# wait til jobs are done, which will never happen since they're infinite loops :)
executor.shutdown(wait=True)

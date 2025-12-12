import datetime
import logging
import os

import dateparser
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from services import db

logger = logging.getLogger(__name__)

DEFAULT_DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")

class MonitorBase:
    def __init__(self, symbol, press_release_url=None):
        self.symbol = symbol.upper()
        self.press_release_url =\
            press_release_url.lower() if press_release_url else None

    def start_web_driver(self, headless: bool = True):
        logger.debug(f"{self.symbol} starting Chrome WebDriver")
        options = Options()
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        if headless:
            options.add_argument("--headless=new")
        driver = webdriver.Chrome(
            options=options,
            service=ChromeService(ChromeDriverManager().install())
        )
        logger.debug(f"{self.symbol} Chrome WebDriver started")
        return driver

    def get_existing_titles(self):
        return db.get_titles_for_symbol(self.symbol)

    def fetch_news_articles(self, driver=None):
        raise NotImplementedError("fetch_news_articles must be implemented by a subclass")

    def parse_date(self, date_str: str) -> datetime.date:
        return dateparser.parse(date_str).date()

    def download_file(self, url, dest_dir=DEFAULT_DOWNLOAD_DIR, 
                    session=None, timeout=30):
        session = session or requests.Session()
        logger.info(f"Downloading file from {url}")
        try:
            response = session.get(url, stream=True, timeout=timeout)
            response.raise_for_status()
            filename = "download-{}-{}.pdf"
            filename = filename.format(self.symbol,
                                       datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
            os.makedirs(dest_dir, exist_ok=True)

            # ensure unique filename
            dest_path = os.path.join(dest_dir, filename)
            base, ext = os.path.splitext(dest_path)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = f"{base}_{counter}{ext}"
                counter += 1

            logger.debug(f"Attempting to save {dest_path}")
            with open(dest_path, 'wb') as fp:
                for chunk in response.iter_content(chunk_size=8192):
                    fp.write(chunk)
            logger.info(f"Saved {url} -> {dest_path}")
            return dest_path
        
        except Exception as e:
            logger.warning(f"Failed to get {url}: {e}")
            return None

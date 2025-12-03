from datetime import datetime
import logging
import os

import pymupdf4llm
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

DEFAULT_DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")

class CaprMonitor:
    def __init__(self):
        self.symbol = "CAPR"
        self.news_url = "https://www.capricor.com/investors/news-events/press-releases"

    def fetch_news_articles(self):
        logger.debug("Starting Chrome WebDriver")
        options = Options()
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        driver = webdriver.Chrome(
            options=options,
            service=ChromeService(ChromeDriverManager().install())
        )
        logger.debug("Chrome WebDriver started")
        driver.get(self.news_url)
        container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "mainContent"))
        )
        articles = container.find_elements(By.TAG_NAME, "article")
        article_data = []
        for article in articles:
            try:
                date = article.find_element(By.TAG_NAME, "time").text
                a = article.find_element(By.TAG_NAME, "a")
                title = a.text.strip()
                url = a.get_attribute("href")
                article_data.append({
                    "date": date,
                    "title": title,
                    "url": url,
                })
            except Exception as e:
                logger.warning(f"Error processing article: {e}")
        for a in article_data:
            try:
                driver.get(a['url'])
                a['document_url'] = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.LINK_TEXT, "Download as PDF"))
                ).get_attribute("href")
            except Exception as e:
                logger.warning(f"{type(e)} occurred getting pdf link for article {a['title'][:32]}:\n{e}")
        driver.quit()
        for a in article_data:
            try:
                a['content'] = pymupdf4llm.to_markdown(
                    self.download_file(a['document_url'])
                )
            except Exception as e:
                logging.warning(f"{type(e)} occurred while loading article {a['title'][:32]}:\n{e}")
        return article_data

    def download_file(self, url, dest_dir=DEFAULT_DOWNLOAD_DIR, 
                    session=None, timeout=30):
        session = session or requests.Session()
        logger.info(f"Downloading file from {url}")
        try:
            response = session.get(url, stream=True, timeout=timeout)
            response.raise_for_status()
            filename = "download-{}-{}.pdf"
            filename = filename.format(self.symbol,
                                       datetime.now().strftime('%Y%m%d%H%M%S'))
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

import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class AgioMonitor:
    def __init__(self):
        self.symbol = "AGIO"
        self.news_url = "https://investor.agios.com/news-events/press-releases"

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
            EC.presence_of_element_located((By.TAG_NAME, "article"))
        )
        articles = container.find_elements(By.TAG_NAME, "article")
        article_data = []
        for article in articles:
            try:
                date = article.find_element(
                    By.CLASS_NAME, "nir-widget--news--date-time"
                ).text
                title = article.find_element(
                    By.CLASS_NAME, "nir-widget--news--headline"
                ).text
                url = article.find_element(
                    By.LINK_TEXT, "View PDF"
                ).get_attribute("href")
                article_data.append({
                    "date": date,
                    "title": title,
                    "document_url": url,
                })
            except Exception as e:
                logger.warning(f"Error processing article: {e}")
        return article_data
        
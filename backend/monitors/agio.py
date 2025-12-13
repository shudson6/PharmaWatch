import datetime
import logging
import os

import pymupdf4llm
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from monitors import MonitorBase

class AgioMonitor(MonitorBase):
    def __init__(self,
                 symbol = "AGIO",
                 press_release_url = "https://investor.agios.com/news-events/press-releases",
                 ):
        super().__init__(symbol, press_release_url)

    def fetch_news_articles(self, driver=None):
        is_our_driver = driver is None
        existing_titles = self.get_existing_titles()
        driver = driver or self.start_web_driver()
        driver.get(self.press_release_url)
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
                if (title, self.parse_date(date)) not in existing_titles:
                    article_data.append({
                        "date": date,
                        "title": title,
                        "document_url": url,
                    })
            except Exception as e:
                self.logger.warning(f"Error processing article: {e}")
        is_our_driver and driver.quit()
        for a in article_data:
            try:
                a['content'] = pymupdf4llm.to_markdown(
                    self.download_file(a['document_url'])
                )
                a['content-type'] = "text/markdown"
                a['retrieved_ts'] = datetime.datetime.now()
            except Exception as e:
                logging.warning(f"{type(e)} occurred while loading article {a['title'][:32]}:\n{e}")
        return article_data

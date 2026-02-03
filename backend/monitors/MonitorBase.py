import datetime
import logging
import os

from bs4 import BeautifulSoup
import dateparser
from lxml import etree
import pymupdf.layout
import pymupdf4llm
import requests

from services import db

DEFAULT_DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")

class MonitorBase:

    def __init__(self, symbol: str, search_params=None):
        self.symbol = symbol.upper()
        self.search_params = search_params or {}
        self.logger = logging.getLogger('.'.join([self.__module__, self.__class__.__name__]))

    def get_existing_titles(self):
        return db.get_titles_for_symbol(self.symbol)

    def fetch_news_articles(self, driver=None):
        resp = requests.get(self.search_params.get("url"))
        soup = BeautifulSoup(resp.content, "html.parser")
        dom = etree.HTML(str(soup))
        articles = dom.xpath(self.search_params.get("article_xpath"))
        article_data = []
        for article in articles:
            date_el = article.xpath(self.search_params.get("date_xpath"))[0]
            date = date_el.text or date_el.findtext(".//")
            title_el = article.xpath(self.search_params.get("title_xpath"))[0]
            title = title_el.text or title_el.findtext(".//")
            url = article.xpath(self.search_params.get("url_xpath"))[0]
            article_data.append({
                "date": date.strip(),
                "title": title.strip(),
                "document_url": url,
            })
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

    def parse_date(self, date_str: str) -> datetime.date:
        return dateparser.parse(date_str).date()

    def download_file(self, url, dest_dir=DEFAULT_DOWNLOAD_DIR, 
                    session=None, timeout=30):
        session = session or requests.Session()
        self.logger.info(f"Downloading file from {url}")
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

            self.logger.debug(f"Attempting to save {dest_path}")
            with open(dest_path, 'wb') as fp:
                for chunk in response.iter_content(chunk_size=8192):
                    fp.write(chunk)
            self.logger.info(f"Saved {url} -> {dest_path}")
            return dest_path
        
        except Exception as e:
            self.logger.warning(f"Failed to get {url}: {e}")
            return None

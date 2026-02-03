import datetime
import logging
import os

from bs4 import BeautifulSoup
import dateparser
from lxml import etree
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

    def _find_articles_lxml(self, dom):
        """Find articles using lxml/xpath from search_params."""
        params = self.search_params

        # Find container first if specified
        if params.get("container_id"):
            containers = dom.xpath(f"//*[@id='{params['container_id']}']")
            if not containers:
                return []
            container = containers[0]
        elif params.get("container_class"):
            containers = dom.xpath(f"//*[contains(@class, '{params['container_class']}')]")
            if not containers:
                return []
            container = containers[0]
        else:
            container = dom

        # Find articles by tag or xpath
        if params.get("article_tag"):
            articles = container.xpath(f".//{params['article_tag']}")
        elif params.get("article_xpath"):
            xpath = params["article_xpath"]
            # If we have a container, make xpath relative
            if container is not dom and xpath.startswith("//"):
                xpath = "." + xpath
            articles = container.xpath(xpath)
        else:
            articles = []

        return articles

    def _extract_text(self, element, xpath):
        """Extract text from element using xpath, handling various cases."""
        results = element.xpath(xpath)
        if not results:
            return None

        result = results[0]
        # If result is a string (from @attr), return it directly
        if isinstance(result, str):
            return result.strip()

        # Otherwise it's an element, get its text content
        text = result.text or result.xpath("string(.)") or ""
        if isinstance(text, list):
            text = text[0] if text else ""
        return text.strip()

    def _extract_date(self, article):
        """Extract date from article element, handling date_join if needed."""
        params = self.search_params
        date_xpath = params.get("date_xpath")

        if params.get("date_join"):
            # Multiple elements need to be joined
            date_elements = article.xpath(date_xpath)
            date_parts = []
            for el in date_elements:
                text = el.text or el.xpath("string(.)") or ""
                if isinstance(text, list):
                    text = text[0] if text else ""
                if text.strip():
                    date_parts.append(text.strip())
            return " ".join(date_parts)
        else:
            return self._extract_text(article, date_xpath)

    def _extract_url(self, article, base_url):
        """Extract document URL from article, handling pdf_link_text if no url_xpath."""
        params = self.search_params

        if params.get("url_xpath"):
            url = self._extract_text(article, params["url_xpath"])
            if url:
                # Handle relative URLs
                if url.startswith("/"):
                    from urllib.parse import urlparse
                    parsed = urlparse(base_url)
                    url = f"{parsed.scheme}://{parsed.netloc}{url}"
                return url

        # Try pdf_link_text to find link directly on listing page
        if params.get("pdf_link_text") and not params.get("requires_article_visit"):
            link_text = params["pdf_link_text"]
            links = article.xpath(f".//a[contains(text(), '{link_text}')]/@href")
            if links:
                url = links[0]
                if url.startswith("/"):
                    from urllib.parse import urlparse
                    parsed = urlparse(base_url)
                    url = f"{parsed.scheme}://{parsed.netloc}{url}"
                return url

        return None

    def _fetch_with_requests(self):
        """Fetch articles using requests/lxml (no JavaScript required)."""
        params = self.search_params
        url = params.get("url")
        existing_titles = self.get_existing_titles()

        resp = requests.get(url)
        soup = BeautifulSoup(resp.content, "html.parser")
        dom = etree.HTML(str(soup))

        articles = self._find_articles_lxml(dom)
        self.logger.debug(f"Found {len(articles)} articles on page")

        article_data = []
        for article in articles:
            try:
                date = self._extract_date(article)
                title = self._extract_text(article, params.get("title_xpath"))
                doc_url = self._extract_url(article, url)

                if not title or not date:
                    continue

                if (title, self.parse_date(date)) in existing_titles:
                    continue

                article_data.append({
                    "date": date,
                    "title": title,
                    "document_url": doc_url,
                })
            except Exception as e:
                self.logger.warning(f"Error processing article: {e}")

        return article_data

    def fetch_news_articles(self, driver=None):
        """Fetch news articles based on search_params configuration."""
        params = self.search_params


        article_data = self._fetch_with_requests()

        # Download and convert PDFs to markdown
        for a in article_data:
            try:
                if a.get("document_url"):
                    a['content'] = pymupdf4llm.to_markdown(
                        self.download_file(a['document_url'])
                    )
                    a['content-type'] = "text/markdown"
                    a['retrieved_ts'] = datetime.datetime.now()
            except Exception as e:
                self.logger.warning(f"{type(e)} occurred while loading article {a['title'][:32]}:\n{e}")

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

from datetime import datetime
import json
import logging
import os
from queue import Queue

import requests

from services import db

logger = logging.getLogger(__name__)

_article_queue = Queue()

def queue_article(article: dict):
    _article_queue.put(article)
    logger.debug(f"Article {article['title']} queued for summarization")

def start():
    logger.info("Starting Summarization Service")

    while True:
        article: dict = _article_queue.get(True)
        logger.info(f"Processing article: {article['title']}")
        try:
            summary_data = summarize_article(article)
            logger.info(f"Article {article['title']} processed")
        except Exception as e:
            logger.warning(
                "%s occurred while summarizing article %s",
                type(e), article['title']
            )
            logger.warning(e)
            continue
        logger.debug(f"Saving summary for article {article['title']}")
        try:
            db.save_new_article_summary(
                article['pr_id'], None, None, summary_data['summary'],
                datetime.now(), summary_data['model'], 
                json.dumps(summary_data['prompt'])
            )
            logger.info(f"Summary for {article['title']} saved")
        except Exception as e:
            logger.warning(
                "%s occured while saving article %s. article not saved.",
                type(e), article['title']
            )
            continue

def summarize_article(article: dict):
    summary_prompt = "Summarize the following document in at most {} bullet points:\n\n{}"
    prepared_prompt = summary_prompt.format(
        _determine_summary_length(article['content']),
        article['content']
    )
    payload = { "prompt": [{
        "role": "user",
        "content": prepared_prompt,
    }]}
    logger.info(f"Fetching summary for article {article['title']}")
    response = requests.get(os.getenv("SUMMARY_URL"), json=payload)
    response.raise_for_status()
    response_body = response.json()
    logger.info(f"Summary received for article {article['title']}")
    return {
        "summary": response_body['reply'],
        "model": response_body['model'],
        "prompt": {
            "role": "user",
            "content": summary_prompt,
        }
    }

def _determine_summary_length(content: str):
    length = len(content)
    if length < 10000:
        return 6
    if length < 20000:
        return 8
    return 10

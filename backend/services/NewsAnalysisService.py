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
                article['pr_id'], summary_data['category'],
                summary_data['sentiment'], summary_data['summary'],
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

PROMPT_TEMPLATE = """{}\n\nAnalyze the preceeding article and respond in the \
following JSON format: {{\
"summary": a brief summary highlighting the key points of the article, \
"subject": one or two words that describe the subject of the article \
(Earnings, Clinical Trial, Regulatory Approval, or Other), \
"sentiment": one word description of the overall sentiment of the article \
(Positive, Negative, Neutral)\
}}"""

def summarize_article(article: dict):
    prepared_prompt = PROMPT_TEMPLATE.format(article['content'])
    payload = { "prompt": [{
        "role": "user",
        "content": prepared_prompt,
    }]}
    logger.info(f"Fetching summary for article {article['title']}")
    response = requests.get(os.getenv("SUMMARY_URL"), json=payload)
    response.raise_for_status()
    response_body = response.json()
    reply = json.loads(response_body.get('reply', ''))
    logger.info(f"Summary received for article {article['title']}")
    return {
        "summary": reply['summary'],
        "category": reply['subject'],
        "sentiment": reply['sentiment'],
        "model": response_body['model'],
        "prompt": {
            "role": "user",
            "content": PROMPT_TEMPLATE,
        }
    }

def queue_unsummarized_articles():
    articles = db.get_unsummarized_articles()
    logger.info(f"Queuing {len(articles)} unsummarized articles")
    for article in articles:
        queue_article(article)

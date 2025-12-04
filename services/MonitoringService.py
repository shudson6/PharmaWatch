from monitors.capr import CaprMonitor
import services.db as db

capr = CaprMonitor()
articles = capr.fetch_news_articles()

for a in articles:
    db.save_new_article(
        capr.symbol, a['date'], a['title'], a['content-type'],
        a['content'], a['document_url'], a['retrieved_ts']
    )
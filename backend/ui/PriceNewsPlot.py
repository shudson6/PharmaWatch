from dotenv import load_dotenv
import matplotlib.pyplot as plt

from services import db, StockDataService
import datetime

load_dotenv()


def plot_with_news(symbol: str):
    price_history = StockDataService.fetch_price_history(symbol)[symbol.upper()]
    news_titles = db.get_titles_for_symbol(symbol.upper())
    # build a mapping from date -> list of titles and sentiments (normalize to date objects)
    title_map = {}
    sentiment_map = {}
    for title, d in news_titles:
        if hasattr(d, 'date'):
            key = d.date()
        else:
            # assume it's already a date
            key = d
        title_map.setdefault(key, []).append(title)
        # get sentiment
        article = db.get_article_with_summary(symbol.upper(), title)
        sentiment = article['sentiment'] if article else None
        sentiment_map.setdefault(key, []).append(sentiment)
    catalysts = {d: True for _, d in news_titles}
    print(f"Found {len(catalysts)} catalyst dates for {symbol}")
    price_history.insert(len(price_history.columns), 'Catalyst', price_history.index.map(catalysts).fillna(False))
    plt.figure()
    plot_price_history(price_history)
    plot_volume_history(price_history)
    plot_catalyst_dates(price_history, title_map, sentiment_map)
    plt.show()

def plot_price_history(dataFrame):
    up = dataFrame[dataFrame.Close >= dataFrame.Open]
    down = dataFrame[dataFrame.Close < dataFrame.Open]
    width = 0.9
    width2 = 0.1
    col1 = 'green'
    col2 = 'red'
    plt.bar(up.index, up.Close-up.Open, width, bottom=up.Open, color=col1) 
    plt.bar(up.index, up.High-up.Close, width2, bottom=up.Close, color=col1) 
    plt.bar(up.index, up.Low-up.Open, width2, bottom=up.Open, color=col1) 
    # Plotting down prices of the stock 
    plt.bar(down.index, down.Close-down.Open, width, bottom=down.Open, color=col2) 
    plt.bar(down.index, down.High-down.Open, width2, bottom=down.Open, color=col2) 
    plt.bar(down.index, down.Low-down.Close, width2, bottom=down.Close, color=col2) 
    plt.xticks(rotation=30, ha='right') 


def plot_volume_history(data):
    # let's let volume take up the bottom 10% of the chart
    chartZero = data.Low.min()
    chart10 = (data.High.max() - chartZero) / 10
    maxVolume = data.Volume.max()
    # maxVolume will be 10% of the chart height
    # other volume bars will be proportional to that
    plt.bar(data.index, chart10 * data.Volume / maxVolume, 0.9, bottom=chartZero, color="blue")


def plot_catalyst_dates(data, title_map=None, sentiment_map=None):
    top = data.High.max()
    bottom = data.Low.min()
    height = (top - bottom)
    news_dates = data[data.Catalyst == True]
    print(f"Plotting {len(news_dates)} news dates")
    ax = plt.gca()
    
    # Determine colors based on sentiment
    colors = []
    for idx in news_dates.index:
        try:
            date_key = idx.date()
        except Exception:
            date_key = idx
        sentiments = sentiment_map.get(date_key, []) if sentiment_map else []
        if any(s and s.lower() == 'positive' for s in sentiments):
            colors.append('green')
        elif any(s and s.lower() == 'negative' for s in sentiments):
            colors.append('red')
        else:
            colors.append('#999999')  # neutral color
    
    bars = ax.bar(news_dates.index, height, 0.95, bottom=bottom, color=colors, alpha=0.44)

    # attach title metadata to each bar using the date key (normalize index to date)
    for rect, idx in zip(bars, news_dates.index):
        try:
            date_key = idx.date()
        except Exception:
            date_key = idx
        rect.set_gid(str(date_key))

    # Try to use mplcursors for hover tooltips; fall back to click-based pick handler
    try:
        import mplcursors

        cursor = mplcursors.cursor(bars.patches, hover=True)

        @cursor.connect("add")
        def on_add(sel):
            rect = sel.artist
            key = rect.get_gid()
            titles = title_map.get(datetime.datetime.fromisoformat(key).date(), ["(no title)"]) if key and title_map else ["(no title)"]
            sel.annotation.set_text("\n".join(titles))

    except Exception:
        # fallback: show annotation on pick (click)
        for rect in bars:
            rect.set_picker(True)

        annot = ax.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)

        def on_pick(event):
            rect = event.artist
            key = rect.get_gid()
            try:
                titles = title_map.get(datetime.datetime.fromisoformat(key).date(), ["(no title)"]) if key and title_map else ["(no title)"]
            except Exception:
                titles = ["(no title)"]
            mouseevent = event.mouseevent
            annot.xy = (mouseevent.xdata, mouseevent.ydata)
            annot.set_text("\n".join(titles))
            annot.set_visible(True)
            plt.draw()

        plt.gcf().canvas.mpl_connect('pick_event', on_pick)
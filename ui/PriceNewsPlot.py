from dotenv import load_dotenv
import matplotlib.pyplot as plt

from services import db, StockDataService

load_dotenv()

def plot_with_news(symbol: str):
    price_history = StockDataService.fetch_price_history(symbol)[symbol.upper()]
    news_titles = db.get_titles_for_symbol(symbol.upper())
    catalysts = {d: True for _, d in news_titles}
    print(f"Found {len(catalysts)} catalyst dates for {symbol}")
    price_history.insert(len(price_history.columns), 'Catalyst', price_history.index.map(catalysts).fillna(False))
    plt.figure()
    plot_price_history(price_history)
    plot_volume_history(price_history)
    plot_catalyst_dates(price_history)
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


def plot_catalyst_dates(data):
    top = data.High.max()
    bottom = data.Low.min()
    height = (top - bottom)
    news_dates = data[data.Catalyst == True]
    print(f"Plotting {len(news_dates)} news dates")
    plt.bar(news_dates.index, height, 0.95, bottom=bottom, color="#99999944")
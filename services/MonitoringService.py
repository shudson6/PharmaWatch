import services.db as db

def resolve_monitor_name(symbol: str):
    return f"monitors.{symbol.lower()}.{symbol.capitalize()}Monitor"

watchlist = db.get_watch_list()
for symbol in watchlist:
    print(f"Monitor for {symbol}: {resolve_monitor_name(symbol)}")

from langchain.tools import tool
import yfinance as yf


@tool
def get_stock_data(symbol: str):
    """
    Ambil data market sederhana.
    """
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1mo")

    if hist.empty:
        return "No data found"

    latest = hist.tail(5)

    return latest.to_string()


@tool
def get_indicators(symbol: str):
    """
    Indicator sederhana.
    """
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="3mo")

    if hist.empty:
        return "No indicator data"

    close = hist["Close"]

    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]

    return f"""
SMA20: {sma20}
SMA50: {sma50}
"""

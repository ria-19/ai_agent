import logging

import yfinance as yf

from .base import Tool

logger = logging.getLogger(__name__)

def get_stock_price_function(ticker: str) -> str:
    """Gets the current stock price for a given ticker symbol."""
    
    logger.info(f"Fetching stock price for: {ticker}")
    stock = yf.Ticker(ticker.strip().upper())
    history = stock.history(period="1d")
    
    if history.empty:
        return f"Could not find stock data for ticker '{ticker}'. It may be an invalid symbol."
        
    price = history['Close'].iloc[-1]
    return str(round(price, 2))


get_stock_price_tool = Tool(
    name="get_stock_price",
    description="Gets the current, real-time stock price for a given stock ticker symbol. Input MUST be a valid ticker like 'AAPL' or 'GOOG'.",
    function=get_stock_price_function
)
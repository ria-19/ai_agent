from unittest.mock import patch
import pandas as pd

from src.tools.financial_tools import get_stock_price_function

@patch('src.tools.financial_tools.yf.Ticker')
def test_get_stock_price_success(mock_yf_ticker):
    """
    Tests the successful case where yfinance returns data for a valid ticker.
    It also checks if the input ticker is correctly cleaned (stripped and uppercased).
    """
    # We need to simulate the chained call: yf.Ticker(...).history(...)
    mock_data = {'Close': [298.50, 300.00, 301.25]}
    mock_dataframe = pd.DataFrame(mock_data)
    
    # That object needs a 'history' method, which should return our fake DataFrame.
    mock_yf_ticker.return_value.history.return_value = mock_dataframe
    
    # Call to the function with a messy ticker to test cleaning
    result = get_stock_price_function("  aapl  ")
    
    # The function should return the last 'Close' price, rounded and as a string.
    assert result == "301.25"
    
    # This proves our function stripped the whitespace and uppercased the ticker.
    mock_yf_ticker.assert_called_once_with("AAPL")

@patch('src.tools.financial_tools.yf.Ticker')
def test_get_stock_price_invalid_ticker(mock_yf_ticker):
    """
    Tests the failure case where yfinance returns no data for an invalid ticker.
    """

    mock_empty_dataframe = pd.DataFrame()
    
    # Configure the mock to return this empty DataFrame.
    mock_yf_ticker.return_value.history.return_value = mock_empty_dataframe
    
    invalid_ticker = "INVALID"
    result = get_stock_price_function(invalid_ticker)
    
    # The function should catch the empty DataFrame and return the specific error message.
    expected_error_message = f"Could not find stock data for ticker '{invalid_ticker}'. It may be an invalid symbol."
    assert result == expected_error_message
    
    mock_yf_ticker.assert_called_once_with(invalid_ticker)
from unittest.mock import patch, MagicMock
import requests

from src.tools.web_tools import browse_function

@patch('src.tools.web_tools.requests.get')
def test_browse_success(mock_requests_get):
    """
    Tests the happy path: a successful browse, HTML parsing, and text cleaning.
    """

    fake_html_content = b"""
    <html>
        <head><title>Test Page</title></head>
        <body>
            <script>console.log("This should be removed");</script>
            <h1>Welcome</h1>
            <p>This is the main content.</p>
            <style>.p { color: red; }</style>
        </body>
    </html>
    """
    # A mock response object that mimics the real requests.Response
    mock_response = MagicMock()
    mock_response.content = fake_html_content
    # The raise_for_status method should do nothing in the success case
    mock_response.raise_for_status.return_value = None
    
    # Configure the main mock to return our fake response object
    mock_requests_get.return_value = mock_response
    
    result = browse_function("http://example.com")
    
    # The function should have removed the script/style tags and extracted the text.
    assert result == "Test Page Welcome This is the main content."
    
    mock_requests_get.assert_called_once()
    # Check that the URL was stripped of any potential whitespace
    called_url = mock_requests_get.call_args[0][0]
    assert called_url == "http://example.com"
    # Check that headers were passed
    assert 'headers' in mock_requests_get.call_args[1]

@patch('src.tools.web_tools.requests.get')
def test_browse_content_truncation(mock_requests_get):
    """
    Tests that long content is correctly truncated to the specified max_length.
    """

    long_text = "a" * 10000
    fake_html_content = f"<html><body><p>{long_text}</p></body></html>".encode('utf-8')
    
    mock_response = MagicMock()
    mock_response.content = fake_html_content
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    
    result = browse_function("http://longcontent.com")
    
    expected_truncated_text = ("a" * 8000) + "... (Content truncated due to length)"
    assert len(result) == len(expected_truncated_text)
    assert result == expected_truncated_text

@patch('src.tools.web_tools.requests.get')
def test_browse_http_error(mock_requests_get):
    """
    Tests the handling of an HTTP error (e.g., 404 Not Found).
    This is triggered when response.raise_for_status() raises an error.
    """

    # We configure the mock response's raise_for_status method to raise an HTTPError
    mock_response = MagicMock()
    error_message = "404 Client Error: Not Found"
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(error_message)
    mock_requests_get.return_value = mock_response

    url = "http://example.com/notfound"
    result = browse_function(url)

    # Check that the function caught the error and returned a user-friendly message.
    assert "Error: Could not fetch content from URL" in result
    assert error_message in result

@patch('src.tools.web_tools.requests.get')
def test_browse_request_exception(mock_requests_get):
    """
    Tests the handling of a network-level error (e.g., DNS failure, timeout).
    This is triggered when requests.get() itself raises an error.
    """
    # This time, the main mock itself raises the exception when called.
    error_message = "Failed to establish a new connection"
    mock_requests_get.side_effect = requests.exceptions.RequestException(error_message)
    
    url = "http://no-such-domain.com"
    result = browse_function(url)
    
    assert "Error: Could not fetch content from URL" in result
    assert error_message in result
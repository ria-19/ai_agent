import logging

import requests
from bs4 import BeautifulSoup

from .base import Tool

logger = logging.getLogger(__name__)

def browse_function(url: str) -> str:
    """
    Fetches the clean, readable text content of a single URL.
    """
    
    logging.info(f"Browsing URL: {url}")
    
    try:
        # Set headers to mimic a real browser to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url.strip(), headers=headers, timeout=15)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)

        # Use BeautifulSoup to parse the HTML and extract text
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove irrelevant tags like scripts and styles
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # Get the text, strip leading/trailing whitespace, and remove excessive newlines
        text = ' '.join(soup.stripped_strings)

        # To avoid overwhelming the agent's context window, we truncate the text.
        # This is a simple but critical step for agent stability.
        max_length = 8000
        if len(text) > max_length:
            logging.warning(f"Content from {url} was truncated.")
            return text[:max_length] + "... (Content truncated due to length)"
        
        return text

    except requests.exceptions.RequestException as e:
        logging.error(f"Error browsing URL {url}: {e}")
        return f"Error: Could not fetch content from URL '{url}'. Reason: {e}"
    except Exception as e:
        logging.error(f"An unexpected error occurred while browsing {url}: {e}")
        return "Error: An unexpected error occurred while processing the URL."

web_browse_tool = Tool(
    name="web_browse",
    description="Use this to **dig deeper into a single URL** found from a 'Search' result. It provides the full text content of a webpage, allowing you to find details that are not in the search summary. Input MUST be a single, valid URL.",
    function=browse_function
)
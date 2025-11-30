import logging
import json
import requests
from bs4 import BeautifulSoup

from .base import Tool
from src.llm import GroqInterface

logger = logging.getLogger(__name__)

def _browse_raw_text(url: str) -> str:
    """
    Fetches the clean, readable text content of a single URL. # Post our testing -> Obervation Overload
    The original "dumb" browse function. This will now be a private helper function
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
        # max_length = 8000
        # if len(text) > max_length:
        #     logging.warning(f"Content from {url} was truncated.")
        #     return text[:max_length] + "... (Content truncated due to length)"
        
        return text

    except requests.exceptions.RequestException as e:
        logging.error(f"Error browsing URL {url}: {e}")
        return f"Error: Could not fetch content from URL '{url}'. Reason: {e}"
    except Exception as e:
        logging.error(f"An unexpected error occurred while browsing {url}: {e}")
        return "Error: An unexpected error occurred while processing the URL."

def inquisitive_browse_function(action_input: str) -> str:
    """
    A "smart" browse function. It takes a JSON string with a "url" and a "question",
    browses the URL, and uses a fast LLM to extract the answer to the question.
    """
    try:
        # 1. Parse the structured input
        input_data = json.loads(action_input)
        url = input_data["url"]
        question = input_data["question"]
    except (json.JSONDecodeError, KeyError):
        return "Error: Invalid input format. Please provide a JSON object with 'url' and 'question' keys."

    # 2. Get the raw text content using our helper
    logger.info(f"Performing inquisitive browse on URL: {url} with question: '{question}'")
    raw_text = _browse_raw_text(url)

    if raw_text.startswith("Error:"):
        return raw_text # Pass through any browsing errors

    # 3. Use a fast LLM to extract the specific answer
    # We instantiate a new interface here for this specific task.
    # Using a fast model is crucial for keeping the tool responsive.
    try:
        extractor_llm = GroqInterface(model="llama-3.1-8b-instant")
        
        prompt = (
            "You are a highly efficient information extraction assistant. "
            "You will be given a large body of text and a specific question. "
            "Your task is to answer the question based *only* on the provided text. "
            "If the answer is not found in the text, you MUST respond with 'Information not found.' "
            "Do not use any prior knowledge. Be concise and direct.\n\n"
            f"--- TEXT ---\n{raw_text[:8000]}\n\n" # Truncate for safety
            f"--- QUESTION ---\n{question}"
        )
        
        messages = [{"role": "user", "content": prompt}]
        response = extractor_llm.get_chat_completion(messages)
        return response['content']

    except Exception as e:
        logger.error(f"LLM extraction failed for URL {url}: {e}")
        return f"Error: Failed to extract information with LLM. Reason: {e}"

inquisitive_web_browse_tool = Tool(
    name="inquisitive_web_browse",
    description=(
        "Use this tool when you need to find a *specific piece of information* from a webpage. "
        "It is more effective than a simple web_browse. "
        "The input MUST be a JSON object with two keys: 'url' and 'question'. "
        "Example: {\"url\": \"https://en.wikipedia.org/wiki/Mars\", \"question\": \"What is the atmospheric pressure on Mars?\"}"
    ),
    function=inquisitive_browse_function
)

web_browse_tool = Tool(
    name="web_browse",
    description="Use this to **dig deeper into a single URL** found from a 'Search' result. It provides the full text content of a webpage, allowing you to find details that are not in the search summary. Input MUST be a single, valid URL.",
    function=_browse_raw_text
)
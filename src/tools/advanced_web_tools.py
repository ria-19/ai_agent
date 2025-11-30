import logging
import json
import json_repair
from playwright.sync_api import sync_playwright

from .base import Tool
from ..llm.groq_interface import GroqInterface

logger = logging.getLogger(__name__)

def dynamic_web_reader_function(action_input: str) -> str:
    """
    A "Tier 2" browsing tool that uses a headless browser to render dynamic,
    JavaScript-heavy websites before extracting information.
    """
    try:
        input_data = json_repair.loads(action_input)
        url = input_data["url"]
        question = input_data["question"]
    except (json.JSONDecodeError, KeyError):
        return "Error: Invalid input format. Please provide a JSON object with 'url' and 'question' keys."

    logger.info(f"Performing DYNAMIC browse on URL: {url} with question: '{question}'")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Navigate to the page and wait for it to be fully loaded
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Get the fully rendered HTML content
            content = page.content()
            browser.close()

    except Exception as e:
        logger.error(f"Playwright failed for URL {url}: {e}")
        return f"Error: The dynamic browser failed to load the URL '{url}'. It might be down or blocking automation."

    # Now, use the LLM extraction logic 
    try:
        extractor_llm = GroqInterface(model="qwen/qwen3-32b")
        
        prompt = (
            "You are a highly efficient information extraction assistant. "
            "You will be given the full HTML content of a webpage and a specific question. "
            "Your task is to answer the question based *only* on the provided text. "
            "If the answer is not found, you MUST respond with 'Information not found.' "
            "Do not use any prior knowledge. Be concise and direct.\n\n"
            f"--- HTML CONTENT ---\n{content[:20000]}\n\n" # We can use a larger context here
            f"--- QUESTION ---\n{question}"
        )
        
        messages = [{"role": "user", "content": prompt}]
        response = extractor_llm.get_chat_completion(messages)
        return response['content']

    except Exception as e:
        logger.error(f"LLM extraction failed for dynamic content from URL {url}: {e}")
        return f"Error: Failed to extract information with LLM from the dynamic page. Reason: {e}"

# Define the new tool for the agent
dynamic_web_reader_tool = Tool(
    name="dynamic_web_reader",
    description=(
        "A powerful web browsing tool that can read and understand complex, dynamic websites that use JavaScript. "
        "It is slower and more expensive, so it should be used as a fallback when 'inquisitive_web_browse' fails or returns 'Information not found'. "
        "The input MUST be a JSON object with two keys: 'url' and 'question'."
    ),
    function=dynamic_web_reader_function
)
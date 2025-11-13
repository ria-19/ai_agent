import logging

from ddgs import DDGS
from .base import Tool 

logger = logging.getLogger(__name__)

# --- Calculator ---
def calculator_function(expression: str) -> str:
    """Evaluates a python mathematical expression"""
    
    logger.info(f"Calculator Expression: {expression}")

    # A safer way to eval, but still be careful in real production
    return str(eval(expression, {"__builtins__": None}, {}))

calculator_tool = Tool(
    name="Calculator",
    description="Calculates the result of a mathematical expression. Input MUST be a valid mathematical formula (e.g., '250 * 0.15'). Do NOT include currency symbols, text, or commas.",
    function=calculator_function
)

# --- Search ---
def search_function(query: str) -> str:
    """Performs a web search and returns titles, snippets, and URLs."""
    
    logger.info(f"Search Query: {query}")
    
    with DDGS() as ddgs:
        # The result object contains 'title', 'body', and 'href'
        results = [result for result in ddgs.text(query, max_results=4)]
        if not results:
            return f"No information found for '{query}'."
        
        formatted_results = "\n".join(
            f"[{i+1}] {res['title']}: {res['body']} (URL: {res['href']})" 
            for i, res in enumerate(results)
        )        
        return formatted_results

search_tool = Tool(
    name="Search",
    description="Use this to find information on a topic or to get a list of URLs to investigate. **To avoid ambiguity, make your search query as specific as possible.** For example, search for 'weather on planet Mars' instead of 'Mars weather'.",
    function=search_function
)

# The Finish tool is a system command.
finish_tool = Tool(
    name="Finish",
    description="Use this action when you have the final answer. The Action Input MUST be a complete, user-friendly sentence that answers the user's original question.",
    function=None
)
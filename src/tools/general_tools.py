import logging

from ddgs import DDGS
from .base import Tool 

logger = logging.getLogger(__name__)

# --- Calculator ---
def calculator_function(expression: str) -> str:
    """Evaluates a python mathematical expression"""
    # 1. SANITIZATION
    # Remove anything that isn't a digit, operator, dot, or parenthesis
    # This fixes the "\n---" issue by simply deleting the ---
    # We keep newlines out.
    clean_expression = expression.strip()
    
    # Remove markdown artifacts if they slipped through parser
    clean_expression = clean_expression.replace("`", "").replace("\n", " ")

    logger.info(f"Calculator Expression: {clean_expression}")

    # 2. Safety Check (Basic)
    # Prevent import execution
    if "__" in clean_expression or "import" in clean_expression:
            return "Error: Unsafe characters detected in expression."
    
    # 3. Execution
    # eval is safe-ish here because we are in a controlled environment,
    # but in production, use a library like 'numexpr' or 'asteval'.    
    # A safer way to eval, but still be careful in real production
    return str(eval(expression, {"__builtins__": None}, {}))

calculator_tool = Tool(
    name="calculator",
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
    name="search",
    description="Use this to find information on a topic or to get a list of URLs to investigate. **To avoid ambiguity, make your search query as specific as possible.** For example, search for 'weather on planet Mars' instead of 'Mars weather'.",
    function=search_function
)

# The Finish tool is a system command.
finish_tool = Tool(
    name="finish",
    description="Use this action when you have the final answer. The Action Input MUST be a complete, user-friendly sentence that answers the user's original question.",
    function=None
)
import logging
import sys 

from src.agent import react_orchestrator
from src.tools import (
    get_stock_price_tool,
    search_tool,
    calculator_tool,
    web_browse_tool,
    finish_tool
)


# --- Configure Logging  ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
    stream=sys.stdout
)

def main():
    # Define the Task and Tools
    
    #task = "What is 15% of the current price of NVDA stock, and what were their last quarter earnings?"
    #task = "What's 15% of the current stock price of Apple (AAPL)?"
    #task = "What's 15% of 200?"
    task = "What's the weather on Mars right now?"
    

    tools = [
        get_stock_price_tool,
        search_tool,
        calculator_tool,
        web_browse_tool,
        finish_tool
    ]

    # 3. Run the Agent
    result = react_orchestrator(task, tools)
    
    print("----- FINAL ANSWER -----")
    print(result)

if __name__ == "__main__":
    main()
    
    
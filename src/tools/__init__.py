# This file centralizes the tools from all modules in this package.

from .base import Tool

from .financial_tools import get_stock_price_tool
from .general_tools import calculator_tool, search_tool, finish_tool
from .web_tools import inquisitive_web_browse_tool
from .advanced_web_tools import dynamic_web_reader_tool


# A convenient list of all tools for the agent constructor
all_tools = [
    get_stock_price_tool,
    search_tool,
    calculator_tool,
    inquisitive_web_browse_tool,
    dynamic_web_reader_tool,
    finish_tool,
]

__all__ = [
    "Tool",
    "get_stock_price_tool",
    "search_tool",
    "calculator_tool",
    "finish_tool",
    "inquisitive_web_browse_tool",
    "dynamic_web_reader_tool",
    "all_tools"
]
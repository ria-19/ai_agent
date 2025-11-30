from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.tools.base import Tool

class BaseAgent(ABC):
    """Base interface for all agent architectures"""
    
    # def __init__(self, tools: List[Tool]):
    #     self.tools = tools
    #     # A quick lookup dictionary for tools (name -> tool_instance)
    #     self.tool_dict = {tool.name: tool for tool in self.tools}
    
    @abstractmethod
    def run(self, goal: str, context: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Executes the agent on a specific goal.
        
        Args:
            goal: The user's main task or query.
            context: Optional additional context (e.g., reflections from previous failed attempts).
            
        Returns:
            A dictionary containing:
            - status: "finished" | "max_steps_reached" | "error",
            - final_answer: "The string provided in the 'Finish' action, or None.",
            - trajectory: [
                {"step": 1, "thought": "...", "action": "...", ...},
                ...
                ],
            - error_message: "A description of any terminal error, or None."
        """
        pass
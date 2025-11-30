from abc import ABC, abstractmethod
from typing import List, Dict

class LLMConnectionError(Exception):
    """Custom exception for failures in LLM API calls."""
    pass
# ------------------------


class LLMInterface(ABC):
    """
    Abstract Base Class for all LLM providers.
    Defines the contract that all LLM adapters must follow.
    """
    
    @abstractmethod
    def get_chat_completion(self, messages: List[Dict[str, str]], json_mode: bool = False) -> Dict[str, str]:
        """
        Sends a request to the LLM and returns the response.

        Args:
            messages: A list of message dictionaries conforming to the standard chat format.
            json_mode: If True, request JSON output.

        Returns:
            The assistant's response as a single message dictionary.
        """
        pass
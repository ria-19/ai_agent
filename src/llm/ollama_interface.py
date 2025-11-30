import ollama
import logging
from typing import List, Dict, Any

from .base import LLMInterface, LLMConnectionError

logger = logging.getLogger(__name__)

class OllamaInterface(LLMInterface):
    """
    Concrete implementation for interacting with local Ollama models.
    Handles JSON mode and provides robust, exception-based error handling.
    """
    
    def __init__(self, model: str = "llama3"):
        self.model = model
        try:
            ollama.list()
            logger.info(f"Ollama connection successful. OllamaInterface initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama. Please ensure Ollama is running. Error: {e}")
            raise LLMConnectionError("Could not connect to Ollama service.") from e

    def get_chat_completion(self, messages: List[Dict[str, str]], json_mode: bool = False) -> Dict[str, Any]:
        """
        Gets a chat completion from a local Ollama model.
        Returns:
            A dictionary representing the assistant's response on success.
        Raises:
            LLMConnectionError: If the API call to Ollama fails.
        """        
        try:
            logger.debug(f"Sending request to Ollama with {len(messages)} messages. JSON mode: {json_mode}")
            
            response = ollama.chat(
                model=self.model,
                messages=messages,
                stream=False,
            )
            
            if 'message' not in response or 'content' not in response['message']:
                raise LLMConnectionError(f"Ollama response was malformed. Full response: {response}")
            
            return response['message']

        except ollama.ResponseError as e:
            # Catch specific library errors to pass the actual error message (e.g., 500s)
            logger.error(f"Ollama API Error: {e}")
            raise LLMConnectionError(f"Ollama API Error: {str(e)}") from e

        except Exception as e:
            # Catch generic errors
            logger.error(f"An unexpected error occurred while calling Ollama: {e}", exc_info=True)
            raise LLMConnectionError(f"An unexpected error occurred: {str(e)}") from e
import os
import logging
from typing import Any, List, Dict

from openai import OpenAI, APIError
from .base import LLMInterface

logger = logging.getLogger(__name__)


class GroqInterface(LLMInterface):
    """
    An interface to the Groq API, which is OpenAI-compatible.
    It uses the official 'openai' library for communication.
    """
    def __init__(self, model: str = "qwen/qwen3-32b", api_key: str = None):
        if api_key is None:
            api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set. Please set the environment variable.")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        self.model = model
        logger.info(f"GroqInterface initialized with model: {self.model}")

    def get_chat_completion(self, messages: List[Dict[str, str]], json_mode: bool = False) -> Dict[str, str]:
        try:
            logger.debug(f"Sending request to Groq with {len(messages)} messages. JSON mode: {json_mode}")
            
            response_format = {"type": "json_object"} if json_mode else {"type": "text"}
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format=response_format,
                temperature=0.7, # A bit of creativity can be good for evaluation/reflection
                stream=False,
            )
            
            content = response.choices[0].message.content
            return {"role": "assistant", "content": content}

        except APIError as e:
            logger.error(f"An API error occurred with Groq: {e}")
            error_content = f"Error: The LLM API call failed with status code {e.status_code}. Details: {e.message}"
            return {"role": "assistant", "content": error_content}
        except Exception as e:
            logger.error(f"An unexpected error occurred while calling Groq: {e}", exc_info=True)
            return {"role": "assistant", "content": f"An unexpected error occurred: {str(e)}"}

            

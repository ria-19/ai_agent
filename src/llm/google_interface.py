import os
import logging
from typing import List, Dict

from openai import OpenAI, APIError
from .base import LLMInterface, LLMConnectionError

logger = logging.getLogger(__name__)

class GoogleInterface(LLMInterface):
    """
    An interface to Google Gemini using their OpenAI-compatible endpoint.
    This makes the code identical to Groq/OpenAI interfaces.
    """
    def __init__(self, model: str = "gemini-2.5-flash", api_key: str = None):
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set. Please set the environment variable.")
        
        # MAGIC: Google now allows us to use the OpenAI client!
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        self.model = model
        logger.info(f"GoogleInterface initialized with model: {self.model}")

    def get_chat_completion(self, messages: List[Dict[str, str]], json_mode: bool = False) -> Dict[str, str]:
        try:
            logger.debug(f"Sending request to Google with {len(messages)} messages.")
            
            # Google supports JSON mode, but sometimes requires the word "JSON" in the prompt too.
            # The adapter handles the technical format.
            response_format = {"type": "json_object"} if json_mode else {"type": "text"}
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format=response_format,
                temperature=0, 
                stream=False,
            )
            
            content = response.choices[0].message.content
            return {"role": "assistant", "content": content}

        except APIError as e:
            logger.error(f"Google API Error: {e}")
            raise LLMConnectionError(f"Google API failed with status {e.status_code}: {e.message}")
        except Exception as e:
            logger.error(f"Unexpected error calling Google: {e}", exc_info=True)
            raise LLMConnectionError(f"Unexpected error: {str(e)}")
from .base import LLMInterface, LLMConnectionError
from .ollama_interface import OllamaInterface
from .groq_interface import GroqInterface
from .google_interface import GoogleInterface

def get_llm_interface(provider: str = "ollama", **kwargs) -> LLMInterface:
    """
    Factory function to get an instance of the appropriate LLM interface.

    Args:
        provider: The name of the provider ("ollama", "openai").
        **kwargs: Arguments to pass to the adapter's constructor (e.g., model, api_key).

    Returns:
        An instance of a class that implements LLMInterface.
    """
    if provider.lower() == "ollama":
        return OllamaInterface(**kwargs)
    elif provider.lower() == "groq":
        return GroqInterface(**kwargs)
    elif provider == "google":
        return GoogleInterface(**kwargs)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")

__all__ = [
    "LLMInterface",
    "LLMConnectionError",
    "OllamaInterface",
    "GroqInterface",
    "GoogleInterface",
    "get_llm_interface",
]
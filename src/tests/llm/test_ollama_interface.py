import pytest
from unittest.mock import patch, MagicMock
import ollama

from src.llm.ollama_interface import OllamaInterface, LLMConnectionError


@patch('src.llm.ollama_interface.ollama')
def test_get_chat_completion_success(mock_ollama_lib):
    """ Tests the successful path for get_chat_completion. """
    # Setup
    mock_ollama_lib.chat.return_value = {
        "message": {
            "role": "assistant",
            "content": "This is a successful response."
        }
    }
    
    # We need to mock ollama.list() for the constructor
    mock_ollama_lib.list.return_value = True 
    
    adapter = OllamaInterface(model="test_model")
    messages = [{"role": "user", "content": "Hello"}]
    
    # Execute
    result = adapter.get_chat_completion(messages)
    
    # Assert
    assert result["role"] == "assistant"
    assert result["content"] == "This is a successful response."
    mock_ollama_lib.chat.assert_called_once()


@patch('src.llm.ollama_interface.ollama')
def test_get_chat_completion_failure_raises_exception(mock_ollama_lib):
    """ Tests that the method raises LLMConnectionError on API failure. """
    # Setup
    # Mock the constructor check
    mock_ollama_lib.list.return_value = True

    # Configure the mock to raise a specific ResponseError
    # We simulate a 500 error from the Ollama server
    mock_ollama_lib.ResponseError = ollama.ResponseError
    mock_ollama_lib.chat.side_effect = ollama.ResponseError("Server not available")
    
    adapter = OllamaInterface(model="test_model")
    messages = [{"role": "user", "content": "Hello"}]
    
    # Execute and Assert
    # The 'match' string checks if the Exception message contains this specific text
    with pytest.raises(LLMConnectionError, match="Ollama API Error: Server not available"):
        adapter.get_chat_completion(messages)

    mock_ollama_lib.chat.assert_called_once()
import pytest
from unittest.mock import patch
from src.llm import get_llm_interface, OllamaInterface, GroqInterface

def test_get_llm_interface_for_ollama():
    """Tests if the factory returns a correctly configured OllamaAdapter."""
    
    interface = get_llm_interface(provider="ollama", model="test_llama")
    
    assert isinstance(interface, OllamaInterface)
    assert interface.model == "test_llama"
    
@patch('src.llm.GroqInterface')
def test_get_llm_interface_for_groq(mock_groq_interface):
    """Tests if the factory returns a correctly configured GroqInterface."""
    
    test_api_key = "sk-12345"
    test_model = "gpt-4"
    interface = get_llm_interface(provider="groq", model=test_model, api_key=test_api_key)
    
    # Verify that the OpenAIAdapter class was called to be instantiated.
    mock_groq_interface.assert_called_once_with(
        api_key=test_api_key, 
        model=test_model
    )
    
    # Verify that the factory returned the mock object that was created.
    # The .return_value of a mock class is the instance that is created.
    assert interface is mock_groq_interface.return_value

def test_get_llm_interface_unknown_provider_raises_error():
    """Tests if the factory raises a ValueError for an unsupported provider."""
    
    with pytest.raises(ValueError) as e:
        get_llm_interface(provider="non_existent_provider")
    
    assert "Unknown LLM provider: non_existent_provider" in str(e.value)
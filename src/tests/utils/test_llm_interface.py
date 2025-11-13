from unittest.mock import patch
from src.utils.llm_interface import prompt_llm

# The @patch decorator intercepts the call to 'ollama.chat' within the
# 'llm_interface' module and replaces it with a mock object.
@patch('src.utils.llm_interface.ollama.chat')
def test_prompt_llm_success(mock_ollama_chat):
    """
    Tests the successful path where ollama.chat returns a valid response.
    We verify that our function correctly parses the response dictionary.
    """
    expected_content = "This is a successful response from the LLM."
    mock_response = {
        'message': {
            'content': expected_content
        }
    }
    mock_ollama_chat.return_value = mock_response
    
    prompt = "What is the capital of France?"
    result = prompt_llm(prompt)
    
    assert result == expected_content
    
    mock_ollama_chat.assert_called_once_with(
        model='llama3',
        messages=[{'role': 'user', 'content': prompt}],
        stream=False
    )

@patch('src.utils.llm_interface.ollama.chat')
def test_prompt_llm_exception(mock_ollama_chat):
    """
    Tests the failure path where ollama.chat raises an exception.
    We verify that our function catches the exception and returns a
    user-friendly error message.
    """
    mock_ollama_chat.side_effect = Exception("Ollama server is not available")
    
    prompt = "This will fail."
    result = prompt_llm(prompt)
    
    assert result == "Error: Could not get a response from the model."
    
    mock_ollama_chat.assert_called_once()
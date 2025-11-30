import pytest
from unittest.mock import Mock, MagicMock

from src.architectures import ReactAgent
from src.llm import LLMConnectionError
from src.tools import Tool

# --- Test Fixture ---

@pytest.fixture
def react_agent_and_mocks():
    """ A pytest fixture to set up a ReactAgent with mocked dependencies. """
    mock_llm = Mock()
    mock_parser = Mock()
    
    mock_search_tool = Mock(spec=Tool)
    mock_search_tool.name = "search"
    mock_search_tool.description = "Searches the web."
    mock_search_tool.execute.return_value = "The capital of France is Paris."

    tools = [mock_search_tool]
    
    agent = ReactAgent(
        llm_interface=mock_llm,
        parser=mock_parser,  
        tools=tools,
        max_steps=5
    )
    yield agent, mock_llm, mock_parser, mock_search_tool

# --- Test Cases ---

def test_run_succeeds_on_immediate_finish(react_agent_and_mocks):
    """ Tests the simplest case: the LLM decides to Finish immediately. """
    agent, mock_llm, mock_parser, _ = react_agent_and_mocks
    
    mock_llm.get_chat_completion.return_value = {"role": "assistant", "content": "Some thought"}
    mock_parser.return_value = ("Thought: I know the answer.", "finish", "The answer is 42.")
    
    result = agent.run(task="What is the meaning of life?")
    
    # --- ASSERTIONS ---
    assert result["status"] == "finished"
    assert result["final_answer"] == "The answer is 42."
    assert len(result["trajectory"]) == 1 # The final "Finish" step is now recorded
    assert result["error_message"] is None
    
    mock_llm.get_chat_completion.assert_called_once()
    mock_parser.assert_called_once_with("Some thought")

def test_run_succeeds_after_one_tool_call(react_agent_and_mocks):
    """ Tests a two-step trajectory: Tool Call -> Finish. """
    agent, mock_llm, mock_parser, mock_search_tool = react_agent_and_mocks
    
    # Use side_effect to provide different mock values for each call
    llm_responses = [
        {"role": "assistant", "content": "content_for_tool_call"},
        {"role": "assistant", "content": "content_for_finish"}
    ]
    mock_llm.get_chat_completion.side_effect = llm_responses
    
    parser_responses = [
        ("Thought: I need to search.", "search", "capital of France"),
        ("Thought: I have the answer now.", "finish", "Paris")
    ]
    mock_parser.side_effect = parser_responses
    
    result = agent.run(task="What is the capital of France?")
    
    # --- ASSERTIONS ---
    assert result["status"] == "finished"
    assert result["final_answer"] == "Paris"
    
    # Verify the trajectory was recorded correctly
    trajectory = result["trajectory"]
    assert len(trajectory) == 2 # Step 1 (Tool) + Step 2 (Finish)
    assert trajectory[0]["action"] == "search"
    assert "The capital of France is Paris." in trajectory[0]["observation"]
    assert trajectory[1]["action"] == "finish"
    
    mock_search_tool.execute.assert_called_once_with("capital of France")
    assert mock_llm.get_chat_completion.call_count == 2
    assert mock_parser.call_count == 2

def test_run_fails_on_max_steps(react_agent_and_mocks):
    """ Tests that the agent terminates correctly when it hits the max_steps limit. """
    agent, mock_llm, mock_parser, _ = react_agent_and_mocks
    
    mock_llm.get_chat_completion.return_value = {"role": "assistant", "content": "loop_content"}
    mock_parser.return_value = ("Thought: I'll just keep searching.", "search", "something")
    
    result = agent.run(task="Get stuck in a loop.")
    
    # --- ASSERTIONS ---
    assert result["status"] == "max_steps_reached"
    assert result["final_answer"] is None
    assert "Agent stopped after reaching the limit" in result["error_message"]
    assert len(result["trajectory"]) == 5 # All 5 failed steps should be recorded
    assert mock_llm.get_chat_completion.call_count == 5

def test_run_handles_llm_connection_error_gracefully(react_agent_and_mocks):
    """ Tests that the agent handles LLM failures and returns a proper error state. """
    agent, mock_llm, mock_parser, _ = react_agent_and_mocks
    
    mock_llm.get_chat_completion.side_effect = LLMConnectionError("Ollama server is down")
    
    result = agent.run(task="A task that will fail.")
    
    # --- ASSERTIONS ---
    assert result["status"] == "error"
    assert result["final_answer"] is None
    assert "Ollama server is down" in result["error_message"]
    assert len(result["trajectory"]) == 1 # The error step is now recorded
    mock_parser.assert_not_called()
    
    mock_parser.assert_not_called()

def test_run_handles_hallucinated_tool(react_agent_and_mocks):
    """ Tests that the agent provides a helpful error message for an unknown tool. """
    agent, mock_llm, mock_parser, _ = react_agent_and_mocks
    
    mock_llm.get_chat_completion.return_value = {"role": "assistant", "content": "bad_tool_content"}
    mock_parser.return_value = ("Thought: I should use a tool that doesn't exist.", "fly_to_moon", "fast")

    # We only need the LLM to respond once for this test
    # The agent will then try to call 'fly_to_moon', fail, and continue the loop
    # We set the second call's parser to Finish to stop the test cleanly
    mock_parser.side_effect = [
        ("Thought: I should use a tool that doesn't exist.", "fly_to_moon", "fast"),
        ("Thought: That didn't work, I'll stop.", "finish", "Okay, I give up.")
    ]
    mock_llm.get_chat_completion.side_effect = [
        {"role": "assistant", "content": "bad_tool_content"},
        {"role": "assistant", "content": "finish_content"}
    ]
    
    result = agent.run(task="Try to use a fake tool.")

    assert result["status"] == "finished"
    trajectory = result["trajectory"]
    assert len(trajectory) == 2
    
    # Check that the observation for the failed step contains a helpful error
    first_step_observation = trajectory[0]["observation"]
    assert "Error: Tool 'fly_to_moon' not found." in first_step_observation
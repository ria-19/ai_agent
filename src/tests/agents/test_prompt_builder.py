import pytest
from src.agent import PromptBuilder
from src.tools import Tool
from src.components.types import EvaluationReport, EvaluationStatus

# --- Reusable Test Data ---

@pytest.fixture
def sample_tools():
    """ Provides a sample list of Tool objects for testing. """
    return [
        Tool(name="Search", description="Searches the web.", function=lambda x: x),
        Tool(name="Calculator", description="Calculates math expressions.", function=lambda x: x)
    ]

@pytest.fixture
def sample_trajectory():
    """ Provides a sample trajectory with a couple of steps. """
    return [
        {"thought": "I need to search for the answer.", "action": "Search", "action_input": "some query", "observation": "Found a result."},
        {"thought": "Now I need to calculate something.", "action": "Calculator", "action_input": "1+1", "observation": "2"}
    ]

@pytest.fixture
def failure_report():
    """ Provides a sample EvaluationReport for a FAILURE status. """
    return EvaluationReport(
        status=EvaluationStatus.FAILURE,
        reason="The agent's final answer was incorrect.",
        confidence=0.95
    )

@pytest.fixture
def partial_success_report():
    """ Provides a sample EvaluationReport for a PARTIAL_SUCCESS status. """
    return EvaluationReport(
        status=EvaluationStatus.PARTIAL_SUCCESS,
        reason="The agent answered the first part of the question but missed the second.",
        confidence=0.85
    )

# --- Tests for the Actor Prompt ---

def test_build_actor_prompt_initial(sample_tools):
    """ Tests the actor prompt with an empty trajectory and reflections. """
    task = "Solve a complex problem."
    reflections = ["Heuristic: Always verify URLs before browsing."]
    
    messages = PromptBuilder.build_actor_prompt(
        task=task,
        tools=sample_tools,
        trajectory=[],
        reflections=reflections
    )
    
    assert isinstance(messages, list)
    assert len(messages) == 1 # Only the system message and the final user prompt
    
    system_msg = messages[0]
    assert system_msg["role"] == "system"
    assert task in system_msg["content"]
    assert "Search: Searches the web." in system_msg["content"] # Check tool formatting
    assert "Lessons from Past Attempts" in system_msg["content"]
    assert reflections[0] in system_msg["content"]

def test_build_actor_prompt_with_trajectory(sample_tools, sample_trajectory):
    """ Tests the actor prompt with a non-empty trajectory. """
    task = "Solve a complex problem."
    
    messages = PromptBuilder.build_actor_prompt(
        task=task,
        tools=sample_tools,
        trajectory=sample_trajectory,
        reflections=None
    )
    
    # 1 (System) + 2*2 (Trajectory turns) = 5 messages
    assert len(messages) == 5
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "assistant"
    assert "Thought: I need to search for the answer." in messages[1]["content"]
    assert messages[2]["role"] == "user"
    assert "Observation: Found a result." in messages[2]["content"]
    assert messages[3]["role"] == "assistant"
    assert messages[4]["role"] == "user"

# --- Test for the Evaluator Prompt ---

def test_build_evaluator_prompt(sample_trajectory):
    """ Tests the evaluator prompt construction. """
    task = "Find two facts."
    actor_result = {
        "final_answer": "Fact 1 is A, and Fact 2 is B.",
        "status": "finished",
        "trajectory": sample_trajectory
    }
    
    messages = PromptBuilder.build_evaluator_prompt(task, actor_result)
    
    assert len(messages) == 2
    system_msg, user_msg = messages
    
    assert system_msg["role"] == "system"
    assert "You are an expert AI evaluator" in system_msg["content"]
    assert "EVALUATION FRAMEWORK" in system_msg["content"]
    
    assert user_msg["role"] == "user"
    assert task in user_msg["content"]
    assert actor_result["final_answer"] in user_msg["content"]
    assert f"Agent took {len(sample_trajectory)} steps" in user_msg["content"]

# --- Tests for the Reflector Prompts ---

def test_reflector_prompt_router(monkeypatch, sample_trajectory, failure_report, partial_success_report):
    """ Tests that the main reflector prompt builder correctly routes to the specialized builders. """
    
    # Mock the specialized builders to see if they are called
    mock_failure = monkeypatch.setattr(PromptBuilder, '_build_failure_prompt', lambda *args, **kwargs: "failure_prompt")
    mock_partial = monkeypatch.setattr(PromptBuilder, '_build_partial_success_prompt', lambda *args, **kwargs: "partial_prompt")
    
    # Test routing to FAILURE
    result_fail = PromptBuilder.build_reflector_prompt("task", sample_trajectory, failure_report)
    assert result_fail == "failure_prompt"

    # Test routing to PARTIAL_SUCCESS
    result_partial = PromptBuilder.build_reflector_prompt("task", sample_trajectory, partial_success_report)
    assert result_partial == "partial_prompt"

def test_build_failure_prompt(sample_trajectory, failure_report):
    """ Tests the specific prompt for a total failure. """
    messages = PromptBuilder._build_failure_prompt("task", sample_trajectory, failure_report)
    
    assert len(messages) == 2
    system_msg, user_msg = messages
    
    assert system_msg["role"] == "system"
    assert "Master Debugger" in system_msg["content"] 
    assert "The AI agent you are mentoring has FAILED" in system_msg["content"]
    
    assert user_msg["role"] == "user"
    assert failure_report.reason in user_msg["content"]
    assert "Thought: I need to search for the answer." in user_msg["content"] # Check trajectory formatting

def test_build_partial_success_prompt(sample_trajectory, partial_success_report):
    """ Tests the specific prompt for a partial success. """
    messages = PromptBuilder._build_partial_success_prompt("task", sample_trajectory, partial_success_report)
    
    assert len(messages) == 2
    system_msg, user_msg = messages
    
    assert system_msg["role"] == "system"
    assert "Senior AI Agent Troubleshooter" in system_msg["content"]
    assert "The agent you are mentoring achieved PARTIAL SUCCESS" in system_msg["content"]
    
    assert user_msg["role"] == "user"
    assert partial_success_report.reason in user_msg["content"]
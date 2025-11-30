import pytest
from unittest.mock import MagicMock, call
from src.architectures import ReflexionAgent
from src.components import EvaluationStatus

# We need a dummy class to mimic the EvaluationReport object
class MockReport:
    def __init__(self, status, confidence):
        self.status = status
        self.confidence = confidence

@pytest.fixture
def mock_components():
    """Sets up mocks for all dependencies."""
    actor = MagicMock()
    evaluator = MagicMock()
    reflector = MagicMock()
    memory = MagicMock()
    
    # Default memory behavior
    memory.get_context.return_value = []
    
    return actor, evaluator, reflector, memory

def test_reflexion_success_first_try(mock_components):
    """Test that agent finishes immediately if the first try is successful."""
    actor, evaluator, reflector, memory = mock_components
    
    # 1. Setup Actor to return a result
    actor.run.return_value = {"final_answer": "42", "trajectory": []}
    
    # 2. Setup Evaluator to return a SUCCESS object (Not a dict!)
    # This specifically tests your fix.
    evaluator.evaluate.return_value = MockReport(EvaluationStatus.FULL_SUCCESS, 1.0)
    
    agent = ReflexionAgent(actor, evaluator, reflector, memory)
    result = agent.run("Task")
    
    # Assertions
    assert result["status"] == "success"
    assert result["final_answer"] == "42"
    assert result["metadata"]["trials_taken"] == 1
    
    # Reflector should NOT have been called
    reflector.reflect.assert_not_called()

def test_reflexion_failure_then_success(mock_components):
    """Test the full loop: Fail -> Reflect -> Retry -> Success."""
    actor, evaluator, reflector, memory = mock_components
    
    # 1. Setup Actor results for 2 calls
    # Call 1: Bad answer
    # Call 2: Good answer
    actor.run.side_effect = [
        {"final_answer": "Bad", "trajectory": ["step1"]}, 
        {"final_answer": "Good", "trajectory": ["step1", "step2"]}
    ]
    
    # 2. Setup Evaluator results for 2 calls
    # Call 1: Failure (High confidence failure triggers reflection)
    # Call 2: Success
    evaluator.evaluate.side_effect = [
        MockReport(EvaluationStatus.FAILURE, 1.0), 
        MockReport(EvaluationStatus.FULL_SUCCESS, 1.0)
    ]
    
    # 3. Setup Reflector
    reflector.reflect.return_value = "Don't be bad."
    
    agent = ReflexionAgent(actor, evaluator, reflector, memory, max_trials=3)
    result = agent.run("Task")
    
    # Assertions
    assert result["status"] == "success"
    assert result["final_answer"] == "Good"
    assert result["metadata"]["trials_taken"] == 2
    
    # Check that reflection happened
    reflector.reflect.assert_called_once()
    memory.add.assert_called_with("Don't be bad.")
    
    # Check that context was passed to actor on second try
    # The first call gets [], the second call gets context from memory
    assert actor.run.call_count == 2

def test_reflexion_max_trials_reached(mock_components):
    """Test that agent stops after max_trials even if failing."""
    actor, evaluator, reflector, memory = mock_components
    
    # Always act
    actor.run.return_value = {"final_answer": "Wrong", "trajectory": []}
    
    # Always fail
    evaluator.evaluate.return_value = MockReport(EvaluationStatus.FAILURE, 1.0)
    
    # Always reflect
    reflector.reflect.return_value = "Try harder."
    
    agent = ReflexionAgent(actor, evaluator, reflector, memory, max_trials=2)
    result = agent.run("Task")
    
    assert result["status"] == "failure_max_trials"
    assert result["metadata"]["trials_taken"] == 2
    assert actor.run.call_count == 2

def test_reflexion_uncertainty_retry(mock_components):
    """Test that low confidence causes a retry WITHOUT reflection."""
    actor, evaluator, reflector, memory = mock_components
    
    actor.run.return_value = {"final_answer": "Maybe?", "trajectory": []}
    
    # Confidence 0.5 is below success (0.95) and failure (0.8) thresholds
    # It is in the "Uncertainty Zone"
    evaluator.evaluate.return_value = MockReport(EvaluationStatus.PARTIAL_SUCCESS, 0.5)
    
    agent = ReflexionAgent(actor, evaluator, reflector, memory, max_trials=2, uncertainty_policy="retry")
    result = agent.run("Task")
    
    # Should run until max trials because it never gets confident enough to stop
    # BUT it should NOT reflect, because it's not confident it failed.
    assert result["status"] == "failure_max_trials"
    reflector.reflect.assert_not_called()
    
def test_is_successful_logic(mock_components):
    """Specific unit test for the logic that crashed previously."""
    actor, evaluator, reflector, memory = mock_components
    agent = ReflexionAgent(actor, evaluator, reflector, memory)
    
    # Case 1: Success + High Confidence -> True
    report = MockReport(EvaluationStatus.FULL_SUCCESS, 0.99)
    assert agent._is_successful(report) is True
    
    # Case 2: Success + Low Confidence -> False
    report = MockReport(EvaluationStatus.FULL_SUCCESS, 0.5)
    assert agent._is_successful(report) is False
    
    # Case 3: Failure + High Confidence -> False
    report = MockReport(EvaluationStatus.FAILURE, 0.99)
    assert agent._is_successful(report) is False
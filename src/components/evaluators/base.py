from abc import ABC, abstractmethod
from typing import Dict, Any
from src.components import EvaluationReport


class BaseEvaluator(ABC):
    """
    Base interface for all Evaluator components.
    
    An Evaluator judges a completed agent trajectory and determines
    the degree of success in achieving the given task.
    
    Design Philosophy:
    - Returns rich evaluation report (not just bool) for intelligent decision-making
    - Supports partial success and confidence scoring
    - Provides actionable feedback for Reflector via 'reason' field
    """

    @abstractmethod
    def evaluate(self, task: str, actor_result: Dict[str, Any]) -> EvaluationReport:
        """
        Evaluates an agent's attempt.

        Args:
            task: The original task given to the agent.
            actor_result: Dictionary from actor's run() containing:
                - status: "finished" | "max_steps_reached" | "error"
                - final_answer: The answer string or None
                - trajectory: List of step dictionaries
                - error_message: Error description or None

        Returns:
            An EvaluationReport dataclass instance:
            {
                "status": EvaluationStatus,
                "reason": str,           # Why this judgment was made
                "confidence": float,     # 0.0 to 1.0
                "metadata": Dict[str, Any]  # Evaluator-specific info (optional)
            }
            
        Examples:
            # Full success:
            {
                "status": EvaluationStatus.FULL_SUCCESS,
                "reason": "All 3 PDFs extracted correctly, growth rate calculation accurate.",
                "confidence": 0.95,
                "metadata": {"tests_passed": 5, "tests_failed": 0}
            }
            
            # Partial success:
            {
                "status": EvaluationStatus.PARTIAL_SUCCESS,
                "reason": "2 of 3 PDFs extracted correctly. PDF 3 had OCR error.",
                "confidence": 0.85,
                "metadata": {"completion_rate": 0.67}
            }
            
            # Failure:
            {
                "status": EvaluationStatus.FAILURE,
                "reason": "Unit test 'test_prime_4' failed: expected False, got True.",
                "confidence": 0.90,
                "metadata": {"failed_test": "test_prime_4"}
            }
        """
        pass
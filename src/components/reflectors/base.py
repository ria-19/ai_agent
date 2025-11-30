from abc import ABC, abstractmethod
from typing import Dict, Any
from src.components.types import EvaluationReport, Reflection


class BaseReflector(ABC):
    """
    Base interface for Reflection components.
    
    A Reflector analyzes a failed (or partially successful) trajectory
    and generates structured lessons to improve future attempts.
    
    Design Philosophy:
    - Status-aware: Different reflection strategies for FAILURE vs PARTIAL_SUCCESS
    - Structured output: Returns dict (not string) for logging and memory
    - Metadata-driven: Uses precise failure data for focused analysis
    - Pure function: Orchestrator decides WHEN to reflect, Reflector decides HOW
    """

    @abstractmethod
    def reflect(self, task: str, actor_result: Dict[str, Any], eval_report: EvaluationReport) -> Reflection:
        """
        Generate reflection from failed/partial attempt.

        Args:
            task: Original task
            actor_result: Full result from actor.run() containing:
                - status: "finished" | "max_steps_reached" | "error"
                - final_answer: The answer string or None
                - trajectory: List of step dictionaries
                - error_message: Error description or None
            eval_report: Evaluation report with status, reason, confidence, metadata

        Returns:
            A Reflection dataclass instance:
            {
                "root_cause_analysis": str,  # Why it failed
                "actionable_heuristic": str,  # What to do differently
                "confidence": float,  # How confident is this reflection (0-1)
                "metadata": Dict[str, Any]  # Optional reflection-specific data
            }

        Examples:
            # For FAILURE:
            {
                "root_cause_analysis": "The 'is_prime' flag was not reset inside the main loop, causing 4 to be incorrectly classified as prime.",
                "actionable_heuristic": "When using status flags inside loops, always reset them at the beginning of each iteration.",
                "confidence": 0.95,
                "metadata": {"error_type": "logic_error", "affected_input": 4}
            }

            # For PARTIAL_SUCCESS:
            {
                "root_cause_analysis": "PDF 3 extraction failed due to OCR error on rotated text.",
                "successful_strategy": "Extraction worked for standard orientation PDFs.",
                "actionable_heuristic": "Before extraction, check PDF orientation and rotate if needed.",
                "confidence": 0.85,
                "metadata": {"completion_rate": 0.67}
            }
        """
        pass
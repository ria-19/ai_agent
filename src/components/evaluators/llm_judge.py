import logging
import json
from typing import Dict, Any

from .base import BaseEvaluator
from src.llm import LLMInterface
from src.agent import PromptBuilder
from src.components import EvaluationReport, EvaluationStatus

logger = logging.getLogger(__name__)

class LLMJudgeEvaluator(BaseEvaluator):
    """
    An advanced evaluator that uses another LLM (the "Judge") to assess
    an agent's performance based on a sophisticated rubric.
    """
    
    def __init__(self, llm_interface: LLMInterface):
        """
        Args:
            llm_interface: The LLM interface used to call the Judge model.
        """
        self.llm = llm_interface
    
    def evaluate(self, task: str, actor_result: Dict[str, Any]) -> EvaluationReport:
        """
        Evaluates the agent's attempt by calling an external LLM Judge.

        This method follows a robust sequence:
        1. Pre-checks for immediate failure conditions (e.g., actor errors).
        2. Builds a detailed, message-based prompt using the PromptBuilder.
        3. Calls the LLM Judge with JSON mode enabled.
        4. Parses and validates the structured response from the Judge.
        5. Returns a final, structured EvaluationReport.
        """
        # --- 1. Pre-checks for Fast Failure ---
        actor_status = actor_result.get("status")
        if actor_status != "finished":
            return EvaluationReport(
                status=EvaluationStatus.FAILURE,
                confidence=1.0, # We are 100% confident this is a failure
                reason=f"Evaluation skipped. Actor did not finish successfully (status: '{actor_status}')."
            )

        final_answer = actor_result.get("final_answer")
        if not final_answer:
            return EvaluationReport(
                status=EvaluationStatus.FAILURE,
                confidence=1.0,
                reason="Actor finished but provided no final answer to evaluate."
            )
            
            
        # --- 2. Build the Prompt ---
        messages = PromptBuilder.build_evaluator_prompt(task, actor_result)
        
        # --- 3. Call the LLM Judge ---
        logger.info("Calling LLM Judge for evaluation...")
        try:
            response_message = self.llm.get_chat_completion(messages, json_mode=True)
            response_content = response_message.get("content", "{}")
            
            # --- 4. Parse and Validate ---
            return self._parse_and_validate_response(response_content)

        except Exception as e:
            logger.error(f"LLM Judge call failed with an unexpected error: {e}", exc_info=True)
            return EvaluationReport(
                status=EvaluationStatus.FAILURE,
                confidence=0.0, # We have zero confidence in this evaluation
                reason=f"Evaluation process failed due to an exception: {e}",
                metadata={"error": str(e)}
            )

    
    def _parse_and_validate_response(self, response_content: str) -> EvaluationReport:
        """
        Parses the JSON string from the LLM, validates its schema,
        and converts it into a structured EvaluationReport.
        """
        try:
            # Attempt to parse the JSON content
            data = json.loads(response_content)
            
            # --- Schema Validation ---
           # --- Check CORE required keys and OPTIONAL keys ---
            core_keys = ["status", "reason", "confidence"]
            if not all(key in data for key in core_keys):
                raise KeyError(f"LLM response is missing core keys: {[k for k in core_keys if k not in data]}")
            
            # Validate the 'status' field against our Enum
            try:
                status_enum = EvaluationStatus(data["status"].upper())
            except ValueError:
                raise ValueError(f"Invalid 'status' value in LLM response: '{data['status']}'")

            # All other keys from the JSON are funneled into metadata.
            metadata = {k: v for k, v in data.items() if k not in core_keys}
            
            confidence = float(data["confidence"])
            # Add bounds check:
            if not 0.0 <= confidence <= 1.0:
                logger.warning(f"Confidence {confidence} out of bounds [0,1]. Clamping.")
                confidence = max(0.0, min(1.0, confidence))  # Clamp to [0,1]
        
            # --- Construct the Report ---
            return EvaluationReport(
                status=status_enum,
                reason=str(data["reason"]),
                confidence=float(data["confidence"]),
                metadata=metadata
            )
            
        except json.JSONDecodeError:
            error_reason = "Evaluation failed: LLM Judge returned a non-JSON response."
            logger.error(f"{error_reason} Content: '{response_content}'")
            return EvaluationReport(status=EvaluationStatus.FAILURE, confidence=0.0, reason=error_reason)
        
        except (KeyError, ValueError) as e:
            error_reason = f"Evaluation failed: LLM Judge returned invalid JSON schema. Error: {e}"
            logger.error(f"{error_reason} Content: '{response_content}'")
            return EvaluationReport(status=EvaluationStatus.FAILURE, confidence=0.0, reason=error_reason)

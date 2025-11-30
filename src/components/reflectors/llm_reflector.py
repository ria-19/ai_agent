import logging
import json
import uuid
from typing import Dict, Any

from .base import BaseReflector
from src.llm import LLMInterface
from src.agent import PromptBuilder
from src.components import Reflection, EvaluationReport

logger = logging.getLogger(__name__)

class LLMReflector(BaseReflector):
    """
    Uses an LLM to generate reflections from failed attempts.
    Implements status-aware reflection (FAILURE vs PARTIAL_SUCCESS).
    """
    
    def __init__(self, llm_interface: LLMInterface):
        self.llm = llm_interface

    def reflect(self, task: str, actor_result: Dict[str, Any], eval_report: EvaluationReport) -> Reflection:  
        """
        Generates reflection from failed/partial attempt.
        
        Args:
            task: Original goal
            actor_result: Full result from actor
            eval_report: Evaluation report
        
        Returns:
            Reflection dataclass
        """
        # --- 1. Pre-check for Fast-Failure ---
        trajectory = actor_result.get("trajectory", [])
        if not trajectory:
            logger.warning("Cannot reflect on an empty trajectory.")
            return self._create_fallback_reflection("The agent failed without taking any actions.")
        
        # --- 2. Build the Prompt ---
        messages = PromptBuilder.build_reflector_prompt(
            task=task,
            trajectory=trajectory,
            eval_report=eval_report
        )
        
        # --- 3. Call the LLM Reflector ---
        logger.info("Calling LLM Reflector for reflection...")
        try:
            response_message = self.llm.get_chat_completion(messages, json_mode=True)
            response_content = response_message.get("content", "{}")
            
            # --- 4. Parse and Validate ---
            return self._parse_and_validate_response(response_content)

        except Exception as e:
            logger.error(f"Reflector call failed with an unexpected error: {e}", exc_info=True)
            return self._create_fallback_reflection(f"Reflection process failed due to an exception: {e}")
        
        
    def _parse_and_validate_response(self, response_content: str) -> Reflection:
        """
        Parses the JSON string from the LLM, validates its schema,
        and converts it into a structured Reflection object.
        """
        try:
            data = json.loads(response_content)
            
            # --- Schema Validation ---
            core_keys = ["root_cause_analysis", "actionable_heuristic", "confidence"]
            if not all(key in data for key in core_keys):
                raise KeyError(f"LLM response is missing core reflection keys: {[k for k in core_keys if k not in data]}")

            # All other keys from the JSON are funneled into metadata.
            metadata = {k: v for k, v in data.items() if k not in core_keys}
            
            confidence = float(data["confidence"])
            if not 0.0 <= confidence <= 1.0:
                logger.warning(f"Reflection confidence {confidence} out of bounds [0,1]. Clamping.")
                confidence = max(0.0, min(1.0, confidence))

            # --- Construct the Reflection ---
            return Reflection(
                id=f"ref_{uuid.uuid4()}",
                actionable_heuristic=str(data["actionable_heuristic"]),
                root_cause_analysis=str(data["root_cause_analysis"]),
                confidence=confidence,
                metadata=metadata
            )

        except json.JSONDecodeError:
            error_reason = "Reflection failed: LLM returned a non-JSON response."
            logger.error(f"{error_reason} Content: '{response_content}'")
            raise ValueError(error_reason) # Raise to be caught by the outer try/except
        
        except (KeyError, ValueError) as e:
            error_reason = f"Reflection failed: LLM returned invalid JSON schema. Error: {e}"
            logger.error(f"{error_reason} Content: '{response_content}'")
            raise ValueError(error_reason) # Raise to be caught by the outer try/except

    def _create_fallback_reflection(self, reason: str) -> Reflection:
        """ Creates a generic, safe fallback reflection when a non-recoverable error occurs. """
        return Reflection(
            id=f"ref_{uuid.uuid4()}",
            actionable_heuristic="The previous attempt failed. A different strategic approach should be taken.",
            root_cause_analysis=f"Reflection generation failed. Reason: {reason}",
            confidence=0.0,
            metadata={"is_fallback": True}
        )  
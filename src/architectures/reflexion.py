"""
AI Agent Framework - Hybrid Architecture
Author: Riya Sangwan
License: MIT (See LICENSE file)
Version: v0.1.0 Stable

This file is part of the AI Agent Framework:
https://github.com/ria-19/ai_agent

TL;DR: Use freely, modify, redistribute, just retain this notice.

Recommended attribution for forks or derivative works.
"""

import logging
from typing import List, Dict, Any, Optional

from .base import BaseAgent
from src.components import EvaluationStatus
from src.components.evaluators import BaseEvaluator
from src.components.reflectors import BaseReflector
from src.components.memory import BaseMemory


logger = logging.getLogger(__name__)

class ReflexionAgent(BaseAgent):
    """
    Reflexion architecture: It wraps an "Actor" agent and enhances it with a strategic, multi-trial
    learning loop involving evaluation and self-reflection.
    """

    def __init__(self,
                 actor: BaseAgent,
                 evaluator: BaseEvaluator,
                 reflector: BaseReflector,
                 memory: BaseMemory,
                 max_trials: int = 3,
                 success_threshold: float = 0.95,
                 failure_threshold: float = 0.80,
                 uncertainty_policy: str = "retry"):
        """
        Initializes the ReflexionAgent.

        Args:
            actor: The inner-loop agent that performs the actions.
            evaluator: The component that judges the actor's performance.
            reflector: The component that generates lessons from failures.
            memory: The working memory component to store reflections.
            max_trials: The maximum number of attempts the agent can make.
            success_threshold: The confidence level required to declare a final success.
            failure_threshold: The confidence level required to trust an evaluation and reflect on it.
            uncertainty_policy: The action to take when confidence is in the uncertainty zone.
                               ("retry", "escalate", "accept").
        """
        self.actor = actor
        self.evaluator = evaluator
        self.reflector = reflector
        self.memory = memory
        if max_trials < 1:
            raise ValueError("max_trials must be at least 1.")
        self.max_trials = max_trials
        self.success_threshold = success_threshold
        self.failure_threshold = failure_threshold
        valid_policies = ["retry", "accept"]
        if uncertainty_policy not in valid_policies:
            raise ValueError(
                f"Unsupported uncertainty_policy: '{uncertainty_policy}'. "
                f"Supported policies are: {valid_policies}"
            )
        self.uncertainty_policy = uncertainty_policy

    def run(self, task: str, context: Optional[List[str]] = None) -> Dict[str, Any]:
        """ Executes the full Reflexion loop: Act -> Evaluate -> Reflect. """
        logger.info(f"--- Starting Reflexion Agent for task: '{task}' ---")
        self.memory.clear()
        trial_history = []
        actor_result = {} # Initialize to ensure it's available for the final report

        for attempt in range(1, self.max_trials + 1):
            logger.info(f"--- Starting Trial {attempt}/{self.max_trials} ---")

            # 1. ACT
            actor_result = self.actor.run(task, context=self.memory.get_context())

            # 2. EVALUATE (with robust error handling)
            try:
                eval_report = self.evaluator.evaluate(task, actor_result=actor_result)
                logger.info(f"Evaluation: {eval_report.status} (Confidence: {eval_report.confidence})")
            except Exception as e:
                logger.error(f"Evaluator failed on attempt {attempt}: {e}", exc_info=True)
                return self._create_final_report("evaluator_error", actor_result, trial_history, attempt)

            reflection_for_this_trial = None

            # 3. DECIDE: The core logic gate
            if self._is_successful(eval_report):
                logger.info("Confident success achieved. Terminating.")
                trial_history.append({"trial_number": attempt, "actor_result": actor_result, "eval_report": eval_report, "reflection": None})
                return self._create_final_report("success", actor_result, trial_history, attempt)

            elif self._should_reflect(eval_report):
                logger.warning(f"Trial {attempt} failed with high confidence. Generating reflection.")
                try:
                    reflection_for_this_trial = self.reflector.reflect(task, actor_result, eval_report)
                    self.memory.add(reflection_for_this_trial)
                except Exception as e:
                    logger.error(f"Reflector failed on attempt {attempt}: {e}", exc_info=True)
                    # Recoverable: Log and continue to the next trial without the new lesson.

            else:
                # This is the Uncertainty Zone
                logger.warning(f"Evaluation in uncertainty zone (Confidence: {eval_report.confidence:.2f}). Policy: '{self.uncertainty_policy}'")
                if self.uncertainty_policy == "accept":
                    trial_history.append({"trial_number": attempt, "actor_result": actor_result, "eval_report": eval_report, "reflection": None})
                    return self._create_final_report("success_by_policy", actor_result, trial_history, attempt)
                # For "retry" or "escalate", we simply continue to the next attempt.
                # A more advanced "escalate" would have logic here.

            # Record the full history of this trial before the next loop
            trial_history.append({
                "trial_number": attempt,
                "actor_result": actor_result,
                "eval_report": eval_report,
                "reflection": reflection_for_this_trial
            })

        # 4. HANDLE MAX TRIALS FAILURE
        logger.error(f"Agent failed to complete task after {self.max_trials} trials.")
        return self._create_final_report("failure_max_trials", actor_result, trial_history, self.max_trials)

    def _is_successful(self, eval_report: Dict) -> bool:
        """ Determines if the trial constitutes a final, successful outcome. """
        is_full_success = eval_report.status == EvaluationStatus.FULL_SUCCESS
        is_confident = eval_report.confidence >= self.success_threshold
        return is_full_success and is_confident

    def _should_reflect(self, eval_report: Dict) -> bool:
        """
        Determines if a reflection should be generated.
        This is a self-contained utility that does not need to know the context
        in which it is called, making it robust and reusable.
        """
        # This check is intentionally included. While the main loop's logic
        # makes it seem redundant, it ensures this method is independent and
        # cannot be misused by other parts of the system.
        if self._is_successful(eval_report):
            return False

        # We reflect if the evaluation is confident enough to be a trustworthy
        # learning signal, regardless of whether it's a PARTIAL_SUCCESS or FAILURE.
        is_confident_enough_to_learn = eval_report.confidence >= self.failure_threshold
        return is_confident_enough_to_learn

    def _create_final_report(self, status: str, actor_result: Dict, trial_history: List[Dict], trials: int) -> Dict[str, Any]:
        """ Helper method to create a consistent, rich final report. """
        return {
            "status": status,
            "final_answer": actor_result.get("final_answer"),
            "last_trajectory": actor_result.get("trajectory"),
            "metadata": {
                "trials_taken": trials,
                "full_trial_history": trial_history,
                "final_reflections": self.memory.get_all()
            }
        }
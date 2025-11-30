from typing import List
from .base import BaseMemory
from src.components import Reflection

import logging

logger = logging.getLogger(__name__)

class SimpleMemory(BaseMemory):
    """
    A simple, in-memory, sliding-window buffer for reflections.
    This serves as the "Working Memory" for a single, coherent task.
    """

    def __init__(self, max_size: int = 3, confidence_threshold: float = 0.6):
        if max_size < 1:
            raise ValueError("max_size must be at least 1.")
        self.max_size = max_size
        self.reflections: List[Reflection] = []
        # Confidence threshold for adding a reflection to memory.
        # This prevents the agent from "learning" from low-quality, noisy reflections.
        self.add_threshold = confidence_threshold

    def add(self, reflection: Reflection):
        """
        Adds a new structured reflection to memory if its confidence is
        above the threshold, then prunes the oldest if the buffer exceeds max_size.
        """
        # --- Quality Gate ---
        if reflection.confidence < self.add_threshold:
            logger.debug(
                f"Reflection confidence ({reflection.confidence:.2f}) is below "
                f"threshold ({self.add_threshold}). Discarding."
            )
            return

        logger.info(f"Adding new reflection to memory. Current size: {len(self.reflections)}")
        self.reflections.append(reflection)

        # --- FIFO / Sliding Window Logic ---
        if len(self.reflections) > self.max_size:
            # Remove the oldest reflection (at the beginning of the list)
            removed = self.reflections.pop(0)
            logger.info("Memory full. Removed oldest reflection.")
            logger.debug(f"Removed heuristic: '{removed.actionable_heuristic}'")

            
    def get_context(self) -> str:
        """
        Formats the actionable heuristics from the stored reflections into a
        single string, ready for injection into the actor's prompt.
        """
        if not self.reflections:
            return "" # Return empty string if no reflections have been added

        # We only want the high-signal heuristic in the prompt, not the full analysis.
        heuristics = [r.actionable_heuristic for r in self.reflections]

        header = "--- STRATEGIC REFLECTIONS ---\n" \
                 "Review these lessons from past attempts before proceeding:"
        
        formatted_heuristics = "\n".join(f"- {h}" for h in heuristics)
        
        return f"{header}\n{formatted_heuristics}\n---------------------------\n"

    def get_all(self) -> List[Reflection]:
        """ Returns the full list of stored Reflection objects. """
        return self.reflections

    def clear(self):
        """ Clears the memory buffer. """
        self.reflections = []
from dataclasses import dataclass, field
from typing import Dict, Any
from enum import Enum

class EvaluationStatus(Enum):
    """ An enumeration for the status of an evaluation. """
    FULL_SUCCESS = "FULL_SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILURE = "FAILURE"

@dataclass
class EvaluationReport:
    """ A structured dataclass for the output of an Evaluator. """
    status: EvaluationStatus
    confidence: float
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Reflection:
    """ A structured dataclass for storing a single reflection. """
    id: str  # A unique identifier for this reflection
    root_cause_analysis: str
    actionable_heuristic: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
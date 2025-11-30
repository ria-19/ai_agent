from abc import ABC, abstractmethod
from typing import List
from src.components import Reflection

class BaseMemory(ABC):
    """ The base interface for all memory components. """

    @abstractmethod
    def add(self, reflection: Reflection) -> None:
        """ Adds a new structured reflection to the memory. """
        pass

    @abstractmethod
    def get_context(self) -> str:
        """ Retrieves the formatted memory context for the agent's prompt. """
        pass

    @abstractmethod
    def get_all(self) -> List[Reflection]:
        """ Retrieves all stored reflections as a list of objects. """
        pass

    @abstractmethod
    def clear(self):
        """ Clears all reflections from the memory. """
        pass
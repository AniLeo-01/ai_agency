"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract LLM provider that returns structured Pydantic objects."""

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str = "",
        max_retries: int = 2,
    ) -> T:
        """Generate a structured response from the LLM.

        Args:
            prompt: The user prompt / input requirements.
            response_model: The Pydantic model class to structure the output as.
            system_prompt: System-level instructions for the LLM.
            max_retries: Number of retries on validation failure.

        Returns:
            An instance of response_model populated by the LLM.
        """
        ...

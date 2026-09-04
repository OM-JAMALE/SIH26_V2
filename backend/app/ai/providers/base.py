from abc import ABC, abstractmethod
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_structured(
        self, prompt: str, system_prompt: str, schema_class: Type[T]
    ) -> T:
        """Generate structured output validated against a Pydantic schema class."""
        pass

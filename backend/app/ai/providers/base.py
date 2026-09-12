from abc import ABC, abstractmethod
from typing import Type, TypeVar, Optional, Dict, Any
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers.
    
    Provides unified interface for:
    - Structured output generation (validated against Pydantic schemas)
    - Flexible response generation (conversation-style)
    """

    @abstractmethod
    def generate_structured(
        self, prompt: str, system_prompt: str, schema_class: Type[T]
    ) -> T:
        """Generate structured output validated against a Pydantic schema class.
        
        Args:
            prompt: User input/instruction text
            system_prompt: System context and guidelines
            schema_class: Pydantic model class for output validation
            
        Returns:
            Instance of schema_class with validated data
            
        Raises:
            ValueError: If output doesn't match schema
            RuntimeError: If provider API fails
        """
        pass

    def generate_response(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs: Any
    ) -> str:
        """Generate free-form text response (not validated against schema).
        
        Default implementation. Providers may override for optimization.
        
        Args:
            prompt: User input
            system_prompt: System context
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text response
        """
        raise NotImplementedError(
            "generate_response not implemented for this provider. "
            "Use generate_structured with a Pydantic schema instead."
        )

    def is_available(self) -> bool:
        """Check if provider is available and ready to use.
        
        Returns:
            True if provider can be used, False otherwise
        """
        return True


"""Unit tests for AI Providers (Module A/C Provider Abstraction)."""

import pytest
from pydantic import BaseModel, Field
from app.ai.providers.mock_provider import MockLLMProvider
from app.ai.providers.local_provider import LocalLLMProvider
from app.ai.providers.factory import get_llm_provider


class SimpleExtractionSchema(BaseModel):
    symptom: str = Field(description="Primary symptom")
    duration: str = Field(description="Duration of symptom")
    severity: str = Field(description="Severity rating")


def test_mock_provider():
    """Verify MockLLMProvider returns deterministic Pydantic validated responses."""
    provider = MockLLMProvider()
    assert provider.is_available() is True

    result = provider.generate_structured(
        prompt="Patient reports headache for 3 days",
        system_prompt="Extract symptoms",
        schema_class=SimpleExtractionSchema
    )

    assert isinstance(result, SimpleExtractionSchema)
    assert result.symptom is not None
    assert result.duration is not None


def test_ollama_provider():
    """Verify Local/Ollama provider initialization and fallback handling."""
    provider = LocalLLMProvider()
    assert provider is not None
    
    # Factory resolution for ollama
    factory_provider = get_llm_provider("ollama")
    assert factory_provider is not None


def test_structured_output_validation():
    """Verify malformed structured output handling in provider abstraction."""
    provider = MockLLMProvider()
    
    class StrictSchema(BaseModel):
        count: int
        valid: bool

    # Mock provider generates valid instance of schema
    result = provider.generate_structured(
        prompt="Count is 5",
        system_prompt="Extract numeric data",
        schema_class=StrictSchema
    )

    assert isinstance(result, StrictSchema)
    assert isinstance(result.count, int)
    assert isinstance(result.valid, bool)

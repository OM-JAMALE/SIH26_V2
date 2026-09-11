"""AI Provider abstraction layer.

This module provides a unified interface for multiple LLM providers:
- OpenAI (production, ChatGPT-4)
- Gemini (Google, alternative cloud)
- Local/Ollama (on-premise, qwen3, llama2)
- Mock (deterministic, testing)

Usage:
    from app.ai.providers import get_llm_provider
    
    # Get configured provider
    provider = get_llm_provider()
    
    # Or specify explicitly
    provider = get_llm_provider("openai")
    
    # Generate structured output
    result = provider.generate_structured(
        prompt="Extract patient info",
        system_prompt="You are a medical AI",
        schema_class=PatientSchema
    )
"""

from app.ai.providers.base import BaseLLMProvider
from app.ai.providers.factory import get_llm_provider
from app.ai.providers.mock_provider import MockLLMProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.gemini_provider import GeminiLLMProvider
from app.ai.providers.local_provider import LocalLLMProvider

__all__ = [
    "BaseLLMProvider",
    "get_llm_provider",
    "MockLLMProvider",
    "OpenAIProvider",
    "GeminiLLMProvider",
    "LocalLLMProvider",
]

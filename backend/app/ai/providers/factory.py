from app.ai.providers.base import BaseLLMProvider
from app.ai.providers.mock_provider import MockLLMProvider
from app.ai.providers.gemini_provider import GeminiLLMProvider
from app.ai.providers.local_provider import LocalLLMProvider
from app.core.config import settings


def get_llm_provider(provider_type: str = None) -> BaseLLMProvider:
    provider_name = (provider_type or settings.ai_provider or "mock").lower()

    if provider_name == "gemini":
        return GeminiLLMProvider()

    if provider_name in ["local", "ollama"]:
        return LocalLLMProvider()

    # Default fallback to Mock provider for tests & offline runs
    return MockLLMProvider()


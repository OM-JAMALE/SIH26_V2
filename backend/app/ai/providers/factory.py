"""Provider factory for selecting and initializing LLM providers."""

from app.ai.providers.base import BaseLLMProvider
from app.ai.providers.mock_provider import MockLLMProvider
from app.ai.providers.gemini_provider import GeminiLLMProvider
from app.ai.providers.local_provider import LocalLLMProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.core.config import settings
from app.core.logging import logger


def get_llm_provider(provider_type: str = None) -> BaseLLMProvider:
    """Get LLM provider instance based on configuration.
    
    Provider selection order:
    1. Explicit provider_type parameter
    2. AI_PROVIDER environment variable
    3. settings.ai_provider config
    4. Default to mock for offline/testing
    
    Args:
        provider_type: Override provider type ("openai", "gemini", "local"/"ollama", "mock")
        
    Returns:
        Initialized provider instance
        
    Examples:
        >>> provider = get_llm_provider("openai")  # Use OpenAI
        >>> provider = get_llm_provider()  # Use configured provider
    """
    provider_name = (provider_type or settings.ai_provider or "mock").lower().strip()

    if provider_name == "openai":
        logger.info("Initializing OpenAI provider")
        provider = OpenAIProvider()
        if not provider.is_available():
            logger.warning("OpenAI API key not configured, falling back to mock provider")
            return MockLLMProvider()
        return provider

    if provider_name == "gemini":
        logger.info("Initializing Gemini provider")
        provider = GeminiLLMProvider()
        if not provider.api_key:
            logger.warning("Gemini API key not configured, falling back to mock provider")
            return MockLLMProvider()
        return provider

    if provider_name in ["local", "ollama"]:
        logger.info(f"Initializing Local/Ollama provider ({provider_name})")
        return LocalLLMProvider()

    # Default fallback to Mock provider for tests & offline runs
    logger.info("Using Mock provider (offline/testing mode)")
    return MockLLMProvider()

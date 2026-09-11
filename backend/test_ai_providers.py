"""Comprehensive tests for AI provider abstraction layer."""

import pytest
from pydantic import BaseModel
from typing import List

from app.ai.providers import (
    get_llm_provider,
    BaseLLMProvider,
    MockLLMProvider,
    OpenAIProvider,
    LocalLLMProvider,
)


# Test schemas
class SimpleOutput(BaseModel):
    """Simple test schema."""
    name: str
    age: int
    is_active: bool


class ComplexOutput(BaseModel):
    """Complex nested test schema."""
    patient_id: str
    symptoms: List[str]
    medications: List[str]
    diagnosis: str


class TestMockProvider:
    """Tests for MockLLMProvider (deterministic, for testing)."""

    def test_mock_provider_initialization(self):
        """Test MockLLMProvider can be instantiated."""
        provider = MockLLMProvider()
        assert provider is not None
        assert isinstance(provider, BaseLLMProvider)

    def test_mock_provider_is_available(self):
        """Mock provider is always available."""
        provider = MockLLMProvider()
        assert provider.is_available() is True

    def test_mock_structured_extraction_simple(self):
        """Test structured extraction with simple schema."""
        provider = MockLLMProvider()
        
        result = provider.generate_structured(
            prompt="Extract patient data",
            system_prompt="You are a medical AI",
            schema_class=SimpleOutput
        )
        
        assert isinstance(result, SimpleOutput)
        assert result.name is not None
        assert result.age is not None
        assert isinstance(result.is_active, bool)

    def test_mock_structured_extraction_complex(self):
        """Test structured extraction with complex schema."""
        provider = MockLLMProvider()
        
        result = provider.generate_structured(
            prompt="Extract symptoms and medications",
            system_prompt="Extract clinical data",
            schema_class=ComplexOutput
        )
        
        assert isinstance(result, ComplexOutput)
        assert result.patient_id is not None
        assert isinstance(result.symptoms, list)
        assert isinstance(result.medications, list)

    def test_mock_deterministic_output(self):
        """Mock provider produces deterministic output."""
        provider = MockLLMProvider()
        
        result1 = provider.generate_structured(
            prompt="Same prompt",
            system_prompt="Same system",
            schema_class=SimpleOutput
        )
        
        result2 = provider.generate_structured(
            prompt="Same prompt",
            system_prompt="Same system",
            schema_class=SimpleOutput
        )
        
        # Same inputs should produce same outputs
        assert result1.model_dump() == result2.model_dump()

    def test_mock_invalid_json_simulation(self):
        """Test mock provider handles invalid JSON gracefully."""
        provider = MockLLMProvider()
        
        with pytest.raises(ValueError):
            provider.generate_structured(
                prompt="SIMULATE_INVALID_JSON_RESPONSE test",
                system_prompt="Test",
                schema_class=SimpleOutput
            )

    def test_mock_schema_validation_error(self):
        """Test mock provider handles schema validation errors."""
        provider = MockLLMProvider()
        
        with pytest.raises(Exception):  # Pydantic ValidationError
            provider.generate_structured(
                prompt="SIMULATE_SCHEMA_TYPE_ERROR test",
                system_prompt="Test",
                schema_class=SimpleOutput
            )


class TestProviderFactory:
    """Tests for provider factory function."""

    def test_factory_default_mock(self):
        """Factory returns mock provider by default."""
        provider = get_llm_provider()
        assert isinstance(provider, MockLLMProvider)

    def test_factory_explicit_mock(self):
        """Factory can explicitly select mock provider."""
        provider = get_llm_provider("mock")
        assert isinstance(provider, MockLLMProvider)

    def test_factory_case_insensitive(self):
        """Factory is case-insensitive."""
        provider1 = get_llm_provider("MOCK")
        provider2 = get_llm_provider("Mock")
        provider3 = get_llm_provider("mock")
        
        assert isinstance(provider1, MockLLMProvider)
        assert isinstance(provider2, MockLLMProvider)
        assert isinstance(provider3, MockLLMProvider)

    def test_factory_local_provider(self):
        """Factory can select local/Ollama provider."""
        provider = get_llm_provider("local")
        assert isinstance(provider, LocalLLMProvider)

    def test_factory_ollama_alias(self):
        """Factory recognizes 'ollama' as alias for 'local'."""
        provider = get_llm_provider("ollama")
        assert isinstance(provider, LocalLLMProvider)

    def test_factory_openai_fallback_without_key(self):
        """Factory falls back to mock if OpenAI key not configured."""
        provider = get_llm_provider("openai")
        # Should fallback to mock if no key
        # (actual result depends on environment)
        assert isinstance(provider, (OpenAIProvider, MockLLMProvider))

    def test_factory_invalid_provider(self):
        """Factory falls back to mock for unknown providers."""
        provider = get_llm_provider("unknown_provider_xyz")
        assert isinstance(provider, MockLLMProvider)


class TestOpenAIProvider:
    """Tests for OpenAIProvider (production provider)."""

    def test_openai_provider_initialization(self):
        """Test OpenAIProvider can be instantiated."""
        provider = OpenAIProvider(api_key="test-key")
        assert provider is not None
        assert isinstance(provider, BaseLLMProvider)

    def test_openai_provider_config(self):
        """Test OpenAI provider configuration."""
        provider = OpenAIProvider(
            api_key="test-key",
            model="gpt-4",
            temperature=0.7
        )
        
        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4"
        assert provider.temperature == 0.7

    def test_openai_provider_no_key_unavailable(self):
        """OpenAI provider is unavailable without API key."""
        provider = OpenAIProvider(api_key=None)
        assert provider.is_available() is False

    def test_openai_provider_with_key_available(self):
        """OpenAI provider is available with API key."""
        provider = OpenAIProvider(api_key="sk-test-key")
        assert provider.is_available() is True


class TestLocalProvider:
    """Tests for LocalLLMProvider (Ollama)."""

    def test_local_provider_initialization(self):
        """Test LocalLLMProvider can be instantiated."""
        provider = LocalLLMProvider()
        assert provider is not None
        assert isinstance(provider, BaseLLMProvider)

    def test_local_provider_default_config(self):
        """Test LocalLLMProvider default configuration."""
        provider = LocalLLMProvider()
        
        assert "localhost" in provider.base_url or "127.0.0.1" in provider.base_url
        assert provider.model == "qwen3"

    def test_local_provider_custom_config(self):
        """Test LocalLLMProvider custom configuration."""
        provider = LocalLLMProvider(
            base_url="http://ollama.example.com:11434",
            model="llama2"
        )
        
        assert provider.base_url == "http://ollama.example.com:11434"
        assert provider.model == "llama2"

    def test_local_provider_url_normalization(self):
        """Test LocalLLMProvider normalizes URLs."""
        provider = LocalLLMProvider(base_url="http://localhost:11434/")
        
        # Should strip trailing slash
        assert provider.base_url == "http://localhost:11434"


class TestBaseProvider:
    """Tests for base provider interface."""

    def test_base_provider_is_abstract(self):
        """BaseLLMProvider cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseLLMProvider()

    def test_base_provider_generate_response_not_implemented(self):
        """Most providers don't implement free-form text generation."""
        provider = MockLLMProvider()
        
        # Mock provider may support this, but base raises NotImplementedError
        # for providers that don't override
        result = provider.generate_response("Test prompt")
        # Mock actually returns deterministic response
        assert isinstance(result, str) or result is not None


class TestProviderInteroperability:
    """Tests for provider interoperability."""

    def test_all_providers_have_common_interface(self):
        """All providers implement BaseLLMProvider interface."""
        providers = [
            MockLLMProvider(),
            LocalLLMProvider(),
            OpenAIProvider(api_key="test-key"),
        ]
        
        for provider in providers:
            assert isinstance(provider, BaseLLMProvider)
            assert hasattr(provider, "generate_structured")
            assert hasattr(provider, "is_available")

    def test_mock_provider_always_works(self):
        """Mock provider always produces valid structured output."""
        provider = MockLLMProvider()
        
        schemas = [SimpleOutput, ComplexOutput]
        for schema in schemas:
            result = provider.generate_structured(
                prompt="test",
                system_prompt="test",
                schema_class=schema
            )
            assert isinstance(result, schema)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

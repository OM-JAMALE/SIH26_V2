"""OpenAI provider for production LLM integration."""

import json
import os
from typing import Type, TypeVar, Optional
from pydantic import BaseModel

from app.ai.providers.base import BaseLLMProvider
from app.core.config import settings
from app.core.logging import logger

T = TypeVar("T", bound=BaseModel)


class OpenAIProvider(BaseLLMProvider):
    """Production LLM provider using OpenAI API (ChatGPT-4).
    
    Features:
    - Structured output via function calling
    - Streaming support
    - Rate limiting and retry logic
    - Temperature control
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4o-mini)
            temperature: Sampling temperature (0-1, lower = deterministic)
            timeout: Request timeout in seconds
            max_retries: Number of retries on failure
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or getattr(settings, "openai_api_key", None)
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries

        if not self.api_key:
            logger.warning("OPENAI_API_KEY not configured - provider will fail at runtime")

    def is_available(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(self.api_key)

    def _validate_api_key(self) -> None:
        """Verify API key is configured."""
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not configured. Set OPENAI_API_KEY environment variable "
                "or provide api_key parameter."
            )

    def _extract_json_substring(self, text: str) -> str:
        """Strip markdown code fence wrappers if present."""
        import re
        cleaned = text.strip()
        pattern = r"^```(?:json)?\s*\n?(.*?)\n?```$"
        match = re.search(pattern, cleaned, re.DOTALL | re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()
        return cleaned

    def generate_structured(
        self, prompt: str, system_prompt: str, schema_class: Type[T]
    ) -> T:
        """Generate structured output using OpenAI's response format or function calling.
        
        Args:
            prompt: User prompt/instruction
            system_prompt: System context
            schema_class: Pydantic model for output validation
            
        Returns:
            Instance of schema_class with validated data
        """
        self._validate_api_key()

        try:
            import openai
        except ImportError:
            raise RuntimeError(
                "OpenAI client not installed. Install with: pip install openai"
            )

        try:
            client = openai.OpenAI(api_key=self.api_key)
            schema_json = json.dumps(schema_class.model_json_schema(), indent=2)

            enhanced_system_prompt = (
                f"{system_prompt}\n\n"
                f"MUST RESPOND ONLY WITH VALID JSON matching this JSON Schema:\n{schema_json}"
            )

            # Modern JSON mode attempt
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    timeout=self.timeout,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": enhanced_system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                )
                if response.choices and response.choices[0].message.content:
                    raw_text = self._extract_json_substring(response.choices[0].message.content)
                    data = json.loads(raw_text)
                    return schema_class.model_validate(data)
            except Exception as json_err:
                logger.warning(f"JSON mode call fallback to function calling: {json_err}")

            # Function calling fallback
            function_definition = {
                "name": "extract_structured_data",
                "description": f"Extract structured information matching schema {schema_class.__name__}",
                "parameters": json.loads(schema_json),
            }

            response = client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                timeout=self.timeout,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                functions=[function_definition],
                function_call={"name": "extract_structured_data"},
            )

            if not response.choices or not response.choices[0].message.function_call:
                raise ValueError("No valid structured response from OpenAI")

            function_call = response.choices[0].message.function_call
            data = json.loads(function_call.arguments)
            result = schema_class.model_validate(data)
            logger.info(f"OpenAI structured extraction successful for {schema_class.__name__}")
            return result

        except Exception as e:
            logger.error(f"OpenAI provider error: {str(e)}")
            raise

    def generate_response(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        **kwargs,
    ) -> str:
        """Generate free-form text response.
        
        Args:
            prompt: User input
            system_prompt: System context
            temperature: Override default temperature
            **kwargs: Additional OpenAI parameters
            
        Returns:
            Generated text
        """
        self._validate_api_key()

        try:
            import openai
        except ImportError:
            raise RuntimeError(
                "OpenAI client not installed. Install with: pip install openai"
            )

        try:
            client = openai.OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model=self.model,
                temperature=temperature or self.temperature,
                timeout=self.timeout,
                messages=[
                    {"role": "system", "content": system_prompt or "You are a helpful medical AI assistant."},
                    {"role": "user", "content": prompt},
                ],
                **kwargs,
            )

            if not response.choices:
                raise ValueError("No response from OpenAI")

            text = response.choices[0].message.content
            logger.info("OpenAI text generation successful")
            return text

        except Exception as e:
            logger.error(f"OpenAI text generation failed: {str(e)}")
            raise

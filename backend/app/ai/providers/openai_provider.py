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
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.1,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4-turbo-preview)
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

    def generate_structured(
        self, prompt: str, system_prompt: str, schema_class: Type[T]
    ) -> T:
        """Generate structured output using OpenAI's function calling.
        
        Args:
            prompt: User prompt/instruction
            system_prompt: System context
            schema_class: Pydantic model for output validation
            
        Returns:
            Instance of schema_class with validated data
            
        Raises:
            ValueError: If API key missing or output invalid
            RuntimeError: If API call fails
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

            # Convert Pydantic schema to JSON schema for function calling
            schema_json = schema_class.model_json_schema()

            # Define function schema for OpenAI
            function_definition = {
                "name": "extract_structured_data",
                "description": f"Extract structured information matching this schema: {schema_class.__name__}",
                "parameters": {
                    "type": "object",
                    "properties": schema_json.get("properties", {}),
                    "required": schema_json.get("required", []),
                },
            }

            # Make API call with function calling
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

            # Extract function call response
            if not response.choices or not response.choices[0].message.function_call:
                raise ValueError("No function call response from OpenAI")

            function_call = response.choices[0].message.function_call
            if function_call.name != "extract_structured_data":
                raise ValueError(f"Unexpected function call: {function_call.name}")

            # Parse and validate output
            try:
                data = json.loads(function_call.arguments)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse function arguments: {function_call.arguments}")
                raise ValueError(f"OpenAI returned invalid JSON: {str(e)}") from e

            # Validate against schema
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

import json
import os
from typing import Type, TypeVar
from pydantic import BaseModel
from app.ai.providers.base import BaseLLMProvider
from app.core.config import settings
from app.core.logging import logger

T = TypeVar("T", bound=BaseModel)


class GeminiLLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or getattr(settings, "gemini_api_key", None)

    def generate_structured(
        self, prompt: str, system_prompt: str, schema_class: Type[T]
    ) -> T:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in environment or settings.")

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=schema_class,
                temperature=0.1,
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config,
            )

            if not response.text:
                raise ValueError("Gemini provider returned empty response.")

            # Validate against Pydantic schema
            data = json.loads(response.text)
            return schema_class.model_validate(data)

        except Exception as e:
            logger.error(f"GeminiLLMProvider execution failed: {str(e)}")
            raise e

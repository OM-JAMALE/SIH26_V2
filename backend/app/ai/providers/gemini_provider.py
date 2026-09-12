import json
import os
from typing import Type, TypeVar, Optional
from pydantic import BaseModel
from app.ai.providers.base import BaseLLMProvider
from app.core.config import settings
from app.core.logging import logger

T = TypeVar("T", bound=BaseModel)


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini AI Provider with Pydantic structured output validation."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or getattr(settings, "gemini_api_key", None)
        )

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate_structured(
        self, prompt: str, system_prompt: str, schema_class: Type[T]
    ) -> T:
        if not self.is_available():
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is not configured in environment or settings.")

        # Attempt 1: Using new 'google.genai' SDK
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
                model="gemini-1.5-flash",
                contents=prompt,
                config=config,
            )

            if response and response.text:
                data = json.loads(response.text)
                return schema_class.model_validate(data)
        except Exception as e1:
            logger.debug(f"google.genai SDK attempt failed or not installed: {e1}. Trying google.generativeai fallback...")

        # Attempt 2: Using standard 'google.generativeai' SDK
        try:
            import google.generativeai as genai_legacy

            genai_legacy.configure(api_key=self.api_key)
            model = genai_legacy.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={"temperature": 0.1, "response_mime_type": "application/json"},
                system_instruction=system_prompt,
            )

            full_prompt = (
                f"{prompt}\n\n"
                f"STRICT INSTRUCTION: Respond strictly with valid JSON conforming to this JSON schema:\n"
                f"{json.dumps(schema_class.model_json_schema())}"
            )
            response = model.generate_content(full_prompt)

            if response and response.text:
                clean_text = response.text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()

                data = json.loads(clean_text)
                return schema_class.model_validate(data)
        except Exception as e2:
            logger.error(f"GeminiLLMProvider execution failed across SDKs: {str(e2)}")
            raise e2

        raise ValueError("Gemini provider returned empty response.")

    def generate_multimodal_structured(
        self, prompt: str, system_prompt: str, schema_class: Type[T], media_bytes: bytes, mime_type: str
    ) -> T:
        """Extract structured clinical findings and handwritten OCR text from image or document bytes using Gemini Vision AI."""
        if not self.is_available():
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is not configured in environment or settings.")

        # Attempt 1: Using new 'google.genai' SDK
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            part = types.Part.from_bytes(data=media_bytes, mime_type=mime_type)
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=schema_class,
                temperature=0.1,
            )

            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=[part, prompt],
                config=config,
            )

            if response and response.text:
                data = json.loads(response.text)
                return schema_class.model_validate(data)
        except Exception as e1:
            logger.debug(f"google.genai SDK attempt failed for multimodal OCR: {e1}. Trying google.generativeai fallback...")

        # Attempt 2: Using standard 'google.generativeai' SDK
        try:
            import google.generativeai as genai_legacy

            genai_legacy.configure(api_key=self.api_key)
            model = genai_legacy.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={"temperature": 0.1, "response_mime_type": "application/json"},
                system_instruction=system_prompt,
            )

            part = {"mime_type": mime_type, "data": media_bytes}
            full_prompt = (
                f"{prompt}\n\n"
                f"STRICT INSTRUCTION: Respond strictly with valid JSON conforming to this JSON schema:\n"
                f"{json.dumps(schema_class.model_json_schema())}"
            )
            response = model.generate_content([full_prompt, part])

            if response and response.text:
                clean_text = response.text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()

                data = json.loads(clean_text)
                return schema_class.model_validate(data)
        except Exception as e2:
            logger.error(f"GeminiLLMProvider multimodal execution failed across SDKs: {str(e2)}")

        # Fallback to standard text generate_structured if vision bytes fail
        return self.generate_structured(prompt, system_prompt, schema_class)

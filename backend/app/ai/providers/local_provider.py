import json
import re
import urllib.request
import urllib.error
from typing import Type, TypeVar, Optional
from pydantic import BaseModel

from app.ai.providers.base import BaseLLMProvider
from app.core.config import settings
from app.core.logging import logger

T = TypeVar("T", bound=BaseModel)


class LocalLLMProvider(BaseLLMProvider):
    """Local LLM provider using Ollama REST API (e.g. qwen3 model)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
    ):
        self.base_url = (base_url or getattr(settings, "ollama_base_url", "http://localhost:11434")).rstrip("/")
        self.model = model or getattr(settings, "ollama_model", "qwen3")
        self.timeout = timeout

    def _extract_json_substring(self, text: str) -> str:
        """Strip markdown code fence wrappers or extract JSON content."""
        cleaned = text.strip()
        # Remove ```json ... ``` or ``` ... ``` wrappers
        pattern = r"^```(?:json)?\s*\n?(.*?)\n?```$"
        match = re.search(pattern, cleaned, re.DOTALL | re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()
        return cleaned

    def generate_structured(
        self, prompt: str, system_prompt: str, schema_class: Type[T]
    ) -> T:
        schema_json = json.dumps(schema_class.model_json_schema(), indent=2)
        
        enhanced_system_prompt = (
            f"{system_prompt}\n\n"
            f"CRITICAL REQUIREMENT: You MUST respond ONLY with a single valid JSON object adhering strictly to this JSON Schema:\n"
            f"{schema_json}\n\n"
            f"Do not include any explanations, introductory text, or markdown codeblocks outside the JSON object."
        )

        payload = {
            "model": self.model,
            "system": enhanced_system_prompt,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
            },
        }

        url = f"{self.base_url}/api/generate"
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Ollama API returned HTTP {resp.status}")
                raw_body = resp.read().decode("utf-8")
                res_obj = json.loads(raw_body)
                
                raw_text = res_obj.get("response", "")
                if not raw_text:
                    raise ValueError("Ollama provider returned empty response text.")

                json_str = self._extract_json_substring(raw_text)
                data = json.loads(json_str)

                # Validate against Pydantic schema
                return schema_class.model_validate(data)

        except urllib.error.URLError as e:
            logger.error(f"LocalLLMProvider connection error ({url}): {str(e)}")
            raise RuntimeError(f"Failed to connect to Ollama at {self.base_url}: {str(e)}") from e
        except json.JSONDecodeError as e:
            logger.error(f"LocalLLMProvider JSON decode failure: {str(e)}")
            raise ValueError(f"Local LLM output is not valid JSON: {str(e)}") from e
        except Exception as e:
            logger.error(f"LocalLLMProvider execution failed: {str(e)}")
            raise e

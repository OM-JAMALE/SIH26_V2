import json
import pytest
from unittest.mock import patch, MagicMock
import urllib.error

from app.ai.providers.factory import get_llm_provider
from app.ai.providers.local_provider import LocalLLMProvider
from app.ai.providers.mock_provider import MockLLMProvider
from app.modules.conversation.schemas import StructuredExtraction, ChiefComplaintItem, InformationStatus
from app.modules.conversation.extraction import LLMExtractionProvider
from app.core.config import settings


def test_factory_creates_local_provider():
    provider_local = get_llm_provider("local")
    assert isinstance(provider_local, LocalLLMProvider)
    assert provider_local.model == "qwen3"

    provider_ollama = get_llm_provider("ollama")
    assert isinstance(provider_ollama, LocalLLMProvider)


def test_factory_respects_settings_ai_provider(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "local")
    provider = get_llm_provider()
    assert isinstance(provider, LocalLLMProvider)


def test_local_provider_successful_generation():
    provider = LocalLLMProvider(base_url="http://localhost:11434", model="qwen3")
    
    mock_response_body = {
        "response": json.dumps({
            "extracted_symptoms": [
                {"symptom": "Chest pain", "status": "PRESENT", "details": "Started 2 hours ago"}
            ],
            "denied_symptoms": ["fever"],
            "patient_inquired_diagnosis_or_treatment": False
        })
    }

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(mock_response_body).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = provider.generate_structured(
            prompt="I have chest pain since 2 hours",
            system_prompt="Extract clinical data",
            schema_class=StructuredExtraction,
        )

    assert isinstance(result, StructuredExtraction)
    assert len(result.extracted_symptoms) == 1
    assert result.extracted_symptoms[0].symptom == "Chest pain"
    assert result.extracted_symptoms[0].status == InformationStatus.PRESENT
    assert "fever" in result.denied_symptoms


def test_local_provider_markdown_fences_stripping():
    provider = LocalLLMProvider()

    raw_markdown = "```json\n" + json.dumps({
        "extracted_symptoms": [
            {"symptom": "Headache", "status": "PRESENT"}
        ]
    }) + "\n```"

    mock_response_body = {"response": raw_markdown}
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(mock_response_body).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = provider.generate_structured(
            prompt="Severe headache",
            system_prompt="Extract",
            schema_class=StructuredExtraction,
        )

    assert isinstance(result, StructuredExtraction)
    assert result.extracted_symptoms[0].symptom == "Headache"


def test_local_provider_invalid_json_raises_value_error():
    provider = LocalLLMProvider()

    mock_response_body = {"response": "This is plain text without valid JSON"}
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(mock_response_body).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(ValueError, match="not valid JSON"):
            provider.generate_structured(
                prompt="Test prompt",
                system_prompt="Test system prompt",
                schema_class=StructuredExtraction,
            )


def test_local_provider_connection_error_raises_runtime_error():
    provider = LocalLLMProvider()

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        with pytest.raises(RuntimeError, match="Failed to connect to Ollama"):
            provider.generate_structured(
                prompt="Test prompt",
                system_prompt="Test system prompt",
                schema_class=StructuredExtraction,
            )


def test_llm_extraction_provider_integration_with_local_llm():
    mock_local_llm = MagicMock()
    mock_local_llm.generate_structured.return_value = StructuredExtraction(
        extracted_symptoms=[ChiefComplaintItem(symptom="Fever", status=InformationStatus.PRESENT)]
    )

    extractor = LLMExtractionProvider(llm_provider=mock_local_llm)
    result = extractor.extract(text="I have a fever", current_section="CHIEF_COMPLAINT", socrates_state="")

    assert isinstance(result, StructuredExtraction)
    assert result.extracted_symptoms[0].symptom == "Fever"
    assert mock_local_llm.generate_structured.called

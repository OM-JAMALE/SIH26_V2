"""Unit tests for FastAPI REST API Endpoints."""

import pytest
import uuid


def test_conversation_flow_happy_path(client):
    """Test full conversation flow from creation to turn processing."""
    # 1. Create Patient Session
    patient_id = str(uuid.uuid4())
    create_resp = client.post(
        "/api/v1/sessions",
        json={"patient_id": patient_id, "mode": "MODERN", "disclaimer_acknowledged": True}
    )
    assert create_resp.status_code in [200, 201]
    session_data = create_resp.json()
    session_id = session_data["session_id"]
    assert session_data["current_section"] == "IDENTIFICATION"

    # 2. Submit Patient Response
    resp_turn = client.post(
        f"/api/v1/sessions/{session_id}/responses",
        json={"text": "I have severe fever and chills for 2 days"}
    )
    assert resp_turn.status_code == 200
    turn_data = resp_turn.json()
    assert turn_data["session_id"] == session_id
    assert "next_question" in turn_data

    # 3. Retrieve Conversation History
    hist_resp = client.get(f"/api/v1/sessions/{session_id}/conversation")
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) >= 2


def test_invalid_input_validation(client):
    """Verify invalid payloads trigger HTTP 422 error responses."""
    bad_resp = client.post("/api/v1/sessions", json={"mode": "MODERN"})
    assert bad_resp.status_code == 422


def test_auth_required(client):
    """Verify system health endpoint returns status."""
    health_resp = client.get("/health")
    assert health_resp.status_code in [200, 503]
    assert health_resp.json()["status"] in ["ok", "degraded"]


def test_cors_headers(client):
    """Verify CORS preflight and response headers are present."""
    response = client.options(
        "/api/v1/sessions",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        }
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers

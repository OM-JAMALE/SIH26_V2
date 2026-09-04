def test_api_integration_flow(client):
    # 1. Access root endpoint
    root_res = client.get("/")
    assert root_res.status_code == 200
    assert "X-Request-ID" in root_res.headers

    # 2. Access db health check
    db_res = client.get("/api/v1/health/db")
    assert db_res.status_code == 200
    assert db_res.json()["status"] == "healthy"

    # 3. Request with custom Request ID header
    custom_id = "integration-test-req-999"
    health_res = client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
    assert health_res.headers.get("X-Request-ID") == custom_id
    assert "services" in health_res.json()

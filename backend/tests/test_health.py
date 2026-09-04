def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["health"] == "/api/v1/health"


def test_health_check_endpoint(client):
    response = client.get("/api/v1/health")
    # Status can be 200 or 503 depending on Redis availability in dev
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "database" in data["services"]


def test_db_health_endpoint(client):
    response = client.get("/api/v1/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

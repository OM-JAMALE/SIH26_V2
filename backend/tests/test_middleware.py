def test_request_id_middleware_generated(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time-MS" in response.headers


def test_request_id_middleware_propagated(client):
    custom_request_id = "test-req-id-12345"
    response = client.get("/", headers={"X-Request-ID": custom_request_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_request_id

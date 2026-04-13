from fastapi.testclient import TestClient

from app.api.main import create_app


def test_review_queue_endpoint_returns_200():
    client = TestClient(create_app())
    response = client.get("/api/review/queue")
    assert response.status_code == 200

from fastapi.testclient import TestClient

from crawl4ai_workbench.app import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ui_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert "Crawl4AI Workbench" in response.text


def test_api_rejects_local_target():
    response = client.post("/api/crawl", json={"url": "http://localhost:9090"})
    assert response.status_code == 400

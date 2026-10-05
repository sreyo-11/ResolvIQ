from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)  # no `with`, so the DB lifespan is not triggered


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
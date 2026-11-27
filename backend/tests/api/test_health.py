from fastapi.testclient import TestClient

from handoff.infrastructure.config import Settings
from handoff.infrastructure.main import create_app


def test_health_returns_ok() -> None:
    settings = Settings(
        llm_provider="fake", db_path=":memory:", shift_pattern="3x8", cors_origins=()
    )
    client = TestClient(create_app(settings))

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

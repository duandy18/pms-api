# tests/api/test_health.py
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "pms-api",
        "version": "0.1.0",
    }


def test_read_v1_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/pms/read/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "surface": "pms-read-v1",
    }

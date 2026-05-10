# tests/api/test_db_config.py
from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.session import get_engine
from app.main import app
from app.settings import get_settings


def _clear_settings_cache() -> None:
    get_settings.cache_clear()
    get_engine.cache_clear()


def test_settings_reads_pms_database_url_only(monkeypatch) -> None:
    monkeypatch.setenv("PMS_DATABASE_URL", "postgresql+psycopg://pms:pms@127.0.0.1:5433/pms")
    monkeypatch.setenv("WMS_DATABASE_URL", "postgresql+psycopg://wms:wms@127.0.0.1:5433/wms")
    _clear_settings_cache()

    settings = get_settings()

    assert settings.database_url == "postgresql+psycopg://pms:pms@127.0.0.1:5433/pms"


def test_db_health_without_pms_database_url_returns_503(monkeypatch) -> None:
    monkeypatch.delenv("PMS_DATABASE_URL", raising=False)
    monkeypatch.setenv("WMS_DATABASE_URL", "postgresql+psycopg://wms:wms@127.0.0.1:5433/wms")
    _clear_settings_cache()

    client = TestClient(app)
    response = client.get("/health/db")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_configured",
        "service": "pms-api",
        "database": "unconfigured",
    }


def test_db_health_route_is_mounted() -> None:
    paths = {
        str(getattr(route, "path", ""))
        for route in app.routes
        if isinstance(getattr(route, "path", ""), str)
    }

    assert "/health/db" in paths

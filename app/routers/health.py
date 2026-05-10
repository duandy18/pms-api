# app/routers/health.py
from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.db.session import DatabaseNotConfigured, check_database
from app.settings import get_settings

router = APIRouter(tags=["health"])


@router.get("/health/db")
def db_health():
    settings = get_settings()
    if not settings.database_url:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_configured",
                "service": "pms-api",
                "database": "unconfigured",
            },
        )

    try:
        check_database()
    except DatabaseNotConfigured:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_configured",
                "service": "pms-api",
                "database": "unconfigured",
            },
        )
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "service": "pms-api",
                "database": "unreachable",
                "detail": str(exc),
            },
        )

    return {
        "status": "ok",
        "service": "pms-api",
        "database": "reachable",
    }


__all__ = ["router"]

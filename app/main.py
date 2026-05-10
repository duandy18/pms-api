# app/main.py
from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.health import router as health_router
from app.routers.pms_read_v1 import router as pms_read_v1_router
from app.routers.pms_owner import router as pms_owner_router

PMS_API_VERSION = "0.1.0"

app = FastAPI(
    title="PMS API",
    version=PMS_API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5174",
        "http://localhost:5174",
        "http://127.0.0.1:8002",
        "http://localhost:8002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(pms_read_v1_router)
app.include_router(pms_owner_router)


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "name": "PMS API",
        "version": PMS_API_VERSION,
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "pms-api",
        "version": PMS_API_VERSION,
    }


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}

# app/pms/system/read_v1/services/app_manifest_service.py
from __future__ import annotations

import os

from app.pms.system.read_v1.contracts import (
    PmsSystemAppManifestBuildInfoOut,
    PmsSystemAppManifestOut,
)

PMS_APP_CODE = "pms"
PMS_APP_NAME = "商品管理"
PMS_APP_VERSION = "0.1.0"


def _env_value(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip():
            return value.strip()
    return None


def build_pms_app_manifest() -> PmsSystemAppManifestOut:
    version = _env_value("PMS_APP_VERSION", "APP_VERSION") or PMS_APP_VERSION

    return PmsSystemAppManifestOut(
        app_code=PMS_APP_CODE,
        app_name=PMS_APP_NAME,
        app_type="business_system",
        status="available",
        description="PMS 商品管理系统，负责商品、包装单位、SKU 编码、条码、供应商等主数据能力。",
        default_web_path="/pms/",
        default_api_path="/api/pms",
        local_web_url=_env_value("PMS_LOCAL_WEB_URL") or "http://127.0.0.1:5174",
        local_api_url=_env_value("PMS_LOCAL_API_URL") or "http://127.0.0.1:8005",
        health_url="/healthz",
        db_health_url="/health/db",
        openapi_url="/openapi.json",
        page_catalog_url="/system/read/v1/page-catalog",
        service_capabilities_url="/system/read/v1/service-capabilities",
        service_dependencies_url="/system/read/v1/service-dependencies",
        version=version,
        build_info=PmsSystemAppManifestBuildInfoOut(
            environment=_env_value("PMS_ENV", "ENV") or "dev",
            git_sha=_env_value("PMS_GIT_SHA", "GIT_SHA", "COMMIT_SHA"),
            build_time=_env_value("PMS_BUILD_TIME", "BUILD_TIME"),
        ),
    )


__all__ = [
    "PMS_APP_CODE",
    "PMS_APP_NAME",
    "PMS_APP_VERSION",
    "build_pms_app_manifest",
]

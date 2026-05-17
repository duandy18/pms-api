# app/pms/system/read_v1/repos/service_capability_repo.py
from __future__ import annotations

from sqlalchemy.orm import Session

from app.pms.system.service_auth.models import (
    PmsServiceCapability,
    PmsServiceCapabilityRoute,
)

ServiceCapabilityRow = dict[str, object]
ServiceCapabilityRouteRow = dict[str, object]


class PmsServiceCapabilityReadRepo:
    """
    PMS service capability read repository.

    Boundary:
    - Read only PMS local service auth declaration tables.
    - Do not read ERP tables.
    - Do not infer capabilities from runtime routes.
    - Do not write any table.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_capability_rows(self) -> list[ServiceCapabilityRow]:
        rows = (
            self.db.query(
                PmsServiceCapability.capability_code.label("capability_code"),
                PmsServiceCapability.capability_name.label("capability_name"),
                PmsServiceCapability.resource_code.label("resource_code"),
                PmsServiceCapability.description.label("description"),
                PmsServiceCapability.is_active.label("is_active"),
                PmsServiceCapability.updated_at.label("source_updated_at"),
            )
            .order_by(PmsServiceCapability.capability_code.asc())
            .all()
        )

        return [dict(row._mapping) for row in rows]

    def list_route_rows(self) -> list[ServiceCapabilityRouteRow]:
        rows = (
            self.db.query(
                PmsServiceCapabilityRoute.capability_code.label("capability_code"),
                PmsServiceCapabilityRoute.http_method.label("http_method"),
                PmsServiceCapabilityRoute.route_path.label("route_path"),
                PmsServiceCapabilityRoute.route_name.label("route_name"),
                PmsServiceCapabilityRoute.auth_required.label("auth_required"),
                PmsServiceCapabilityRoute.is_active.label("is_active"),
                PmsServiceCapabilityRoute.created_at.label("source_created_at"),
            )
            .order_by(
                PmsServiceCapabilityRoute.capability_code.asc(),
                PmsServiceCapabilityRoute.http_method.asc(),
                PmsServiceCapabilityRoute.route_path.asc(),
            )
            .all()
        )

        return [dict(row._mapping) for row in rows]


__all__ = [
    "PmsServiceCapabilityReadRepo",
    "ServiceCapabilityRouteRow",
    "ServiceCapabilityRow",
]

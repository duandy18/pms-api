# app/db/metadata.py
from __future__ import annotations

from sqlalchemy import MetaData

from app.db.base import Base


def load_metadata() -> MetaData:
    """
    Load PMS API SQLAlchemy metadata for Alembic.

    Boundary:
    - pms-api owns PMS owner tables.
    - pms-api owns suppliers / supplier_contacts as PMS master data.
    - pms-api also owns its own local auth/navigation runtime tables.
    - pms-api also owns local service-to-service authorization runtime tables.
    - items.supplier_id remains scalar during the WMS supplier stability window.
    - do not import WMS/Procurement/OMS models here.
    """
    import app.pms.items.models  # noqa: F401
    import app.pms.sku_coding.models.sku_coding  # noqa: F401
    import app.pms.suppliers.models  # noqa: F401
    import app.service_auth.models  # noqa: F401
    import app.user.models  # noqa: F401

    return Base.metadata


metadata = load_metadata()

__all__ = ["load_metadata", "metadata"]

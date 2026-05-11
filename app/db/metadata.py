# app/db/metadata.py
from __future__ import annotations

from sqlalchemy import MetaData

from app.db.base import Base


def load_metadata() -> MetaData:
    """
    Load PMS API SQLAlchemy metadata for Alembic.

    Boundary:
    - pms-api owns PMS owner tables.
    - pms-api also owns its own local auth/navigation runtime tables.
    - suppliers remains outside PMS; items.supplier_id is a scalar reference.
    - do not import WMS/Procurement/OMS models here.
    """
    import app.pms.items.models  # noqa: F401
    import app.pms.sku_coding.models.sku_coding  # noqa: F401
    import app.user.models  # noqa: F401

    return Base.metadata


metadata = load_metadata()

__all__ = ["load_metadata", "metadata"]

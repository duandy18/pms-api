# app/db/metadata.py
from __future__ import annotations

from sqlalchemy import MetaData

from app.db.base import Base


def load_metadata() -> MetaData:
    """
    Load PMS owner SQLAlchemy metadata for Alembic.

    Boundary:
    - pms-api owns PMS tables only.
    - suppliers remains outside PMS; items.supplier_id is a scalar reference.
    - do not import WMS/Procurement/OMS models here.
    """
    import app.pms.items.models  # noqa: F401
    import app.pms.sku_coding.models.sku_coding  # noqa: F401

    return Base.metadata


metadata = load_metadata()

__all__ = ["load_metadata", "metadata"]

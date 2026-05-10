# scripts/db_smoke.py
from __future__ import annotations

from app.db.session import check_database
from app.settings import get_settings


def main() -> None:
    settings = get_settings()
    print(f"PMS_DATABASE_URL={settings.database_url}")
    check_database()
    print("pms-api db smoke: OK")


if __name__ == "__main__":
    main()

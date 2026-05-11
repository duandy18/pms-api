#!/usr/bin/env python3
from __future__ import annotations

import os

from sqlalchemy import text

from app.core.security import get_password_hash
from app.db.session import get_session_factory


def ensure_admin(
    *,
    username: str = "admin",
    password: str = "admin123",
    full_name: str = "PMS Admin",
) -> None:
    password_hash = get_password_hash(password)
    session_factory = get_session_factory()

    with session_factory() as session:
        session.execute(
            text(
                """
                INSERT INTO users (username, password_hash, is_active, full_name, phone, email)
                VALUES (:username, :password_hash, TRUE, :full_name, NULL, NULL)
                ON CONFLICT (username) DO UPDATE
                  SET password_hash = EXCLUDED.password_hash,
                      is_active = TRUE,
                      full_name = EXCLUDED.full_name
                """
            ),
            {
                "username": username,
                "password_hash": password_hash,
                "full_name": full_name,
            },
        )

        user_id = session.execute(
            text("SELECT id FROM users WHERE username = :username LIMIT 1"),
            {"username": username},
        ).scalar_one()

        session.execute(
            text("DELETE FROM user_permissions WHERE user_id = :user_id"),
            {"user_id": int(user_id)},
        )
        session.execute(
            text(
                """
                INSERT INTO user_permissions (user_id, permission_id)
                SELECT :user_id, id
                FROM permissions
                WHERE name IN ('page.pms.read', 'page.pms.write')
                """
            ),
            {"user_id": int(user_id)},
        )

        session.commit()


def main() -> None:
    ensure_admin(
        username=os.getenv("ADMIN_USERNAME", "admin"),
        password=os.getenv("ADMIN_PASSWORD", "admin123"),
        full_name=os.getenv("ADMIN_FULL_NAME", "PMS Admin"),
    )
    print("[ensure_admin] done.")


if __name__ == "__main__":
    main()

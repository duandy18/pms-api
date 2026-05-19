# tests/api/test_pms_system_iam_write_api.py
from __future__ import annotations

from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_engine, get_session_factory
from app.main import app
from app.settings import get_settings
from app.user.models.user import User

APPLY_PATH = "/system/write/v1/iam/apply"
VERIFY_PATH = "/system/write/v1/iam/verify"
ERP_HEADER = {"X-Service-Client": "erp-service"}


@pytest.fixture(autouse=True)
def _clear_cached_db_settings() -> Generator[None, None, None]:
    get_settings.cache_clear()
    get_engine.cache_clear()
    yield
    get_engine.cache_clear()
    get_settings.cache_clear()


def _payload(username: str) -> dict:
    return {
        "users": [
            {
                "username": username,
                "full_name": "ERP Managed PMS User",
                "phone": "13900002222",
                "email": f"{username}@example.com",
                "is_active": True,
            }
        ],
        "user_permissions": [
            {
                "username": username,
                "permission_code": "page.pms.read",
                "is_active": True,
            },
            {
                "username": username,
                "permission_code": "page.admin.read",
                "is_active": True,
            },
        ],
    }


def _cleanup_usernames(db: Session, usernames: set[str]) -> None:
    if not usernames:
        return

    db.query(User).filter(User.username.in_(sorted(usernames))).delete(synchronize_session=False)
    db.commit()


@pytest.fixture()
def client_with_pg_db() -> Generator[TestClient, None, None]:
    usernames: set[str] = set()

    with TestClient(app) as client:
        client.usernames_for_cleanup = usernames  # type: ignore[attr-defined]
        yield client

    if usernames:
        session_factory = get_session_factory()
        with session_factory() as db:
            _cleanup_usernames(db, usernames)


def _track_username(client: TestClient, username: str) -> str:
    usernames = getattr(client, "usernames_for_cleanup", None)
    if isinstance(usernames, set):
        usernames.add(username)
    return username


def test_pms_iam_apply_requires_erp_service_client_header(
    client_with_pg_db: TestClient,
) -> None:
    username = f"zz_pms_iam_{uuid4().hex[:10]}"

    response = client_with_pg_db.post(APPLY_PATH, json=_payload(username))

    assert response.status_code == 401
    assert "pms_service_client_required" in response.text


def test_pms_iam_apply_rejects_non_erp_service_client(
    client_with_pg_db: TestClient,
) -> None:
    username = f"zz_pms_iam_{uuid4().hex[:10]}"

    response = client_with_pg_db.post(
        APPLY_PATH,
        headers={"X-Service-Client": "wms-service"},
        json=_payload(username),
    )

    assert response.status_code == 403
    assert "pms_service_permission_write_denied" in response.text


def test_pms_iam_apply_and_verify_desired_state(
    client_with_pg_db: TestClient,
) -> None:
    username = _track_username(client_with_pg_db, f"zz_pms_iam_{uuid4().hex[:10]}")
    payload = _payload(username)

    verify_before = client_with_pg_db.post(VERIFY_PATH, headers=ERP_HEADER, json=payload)
    assert verify_before.status_code == 200, verify_before.text
    assert verify_before.json()["verified"] is False
    assert username in verify_before.json()["missing_users"]

    apply_response = client_with_pg_db.post(APPLY_PATH, headers=ERP_HEADER, json=payload)
    assert apply_response.status_code == 200, apply_response.text

    applied = apply_response.json()
    assert applied["app_code"] == "pms"
    assert applied["applied"] is True
    assert applied["verified"] is True
    assert applied["user_count"] == 1
    assert applied["desired_permission_count"] == 2
    assert applied["missing_users"] == []
    assert applied["missing_permission_codes"] == []
    assert applied["missing_user_permissions"] == []
    assert applied["extra_user_permissions"] == []

    verify_after = client_with_pg_db.post(VERIFY_PATH, headers=ERP_HEADER, json=payload)
    assert verify_after.status_code == 200, verify_after.text
    assert verify_after.json()["verified"] is True


def test_pms_iam_apply_replaces_supplied_user_permissions(
    client_with_pg_db: TestClient,
) -> None:
    username = _track_username(client_with_pg_db, f"zz_pms_iam_{uuid4().hex[:10]}")

    first_payload = _payload(username)
    first_response = client_with_pg_db.post(APPLY_PATH, headers=ERP_HEADER, json=first_payload)
    assert first_response.status_code == 200, first_response.text
    assert first_response.json()["verified"] is True

    second_payload = {
        "users": first_payload["users"],
        "user_permissions": [
            {
                "username": username,
                "permission_code": "page.pms.read",
                "is_active": True,
            }
        ],
    }
    second_response = client_with_pg_db.post(APPLY_PATH, headers=ERP_HEADER, json=second_payload)
    assert second_response.status_code == 200, second_response.text
    assert second_response.json()["verified"] is True

    old_verify = client_with_pg_db.post(VERIFY_PATH, headers=ERP_HEADER, json=first_payload)
    assert old_verify.status_code == 200, old_verify.text
    old_body = old_verify.json()
    assert old_body["verified"] is False
    assert {
        "username": username,
        "permission_code": "page.admin.read",
    } in old_body["missing_user_permissions"]


def test_pms_iam_apply_rejects_unknown_permission_code(
    client_with_pg_db: TestClient,
) -> None:
    username = _track_username(client_with_pg_db, f"zz_pms_iam_{uuid4().hex[:10]}")
    payload = {
        "users": [
            {
                "username": username,
                "is_active": True,
            }
        ],
        "user_permissions": [
            {
                "username": username,
                "permission_code": "page.not_exists.read",
                "is_active": True,
            }
        ],
    }

    response = client_with_pg_db.post(APPLY_PATH, headers=ERP_HEADER, json=payload)

    assert response.status_code == 404
    assert "pms_iam_permission_not_found" in response.text


def test_pms_iam_routes_are_registered_in_openapi() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200, response.text
    paths = response.json()["paths"]

    assert APPLY_PATH in paths
    assert VERIFY_PATH in paths
    assert "post" in paths[APPLY_PATH]
    assert "post" in paths[VERIFY_PATH]

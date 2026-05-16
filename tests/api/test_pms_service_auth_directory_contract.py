# tests/api/test_pms_service_auth_directory_contract.py
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_pms_service_auth_lives_under_pms_system_domain() -> None:
    assert not (ROOT / "app/service_auth").exists()

    expected_files = {
        "app/pms/system/service_auth/__init__.py",
        "app/pms/system/service_auth/models/__init__.py",
        "app/pms/system/service_auth/models/pms_service_client.py",
        "app/pms/system/service_auth/models/pms_service_capability.py",
        "app/pms/system/service_auth/models/pms_service_capability_route.py",
        "app/pms/system/service_auth/models/pms_service_permission.py",
        "app/pms/system/service_auth/repos/__init__.py",
        "app/pms/system/service_auth/repos/pms_service_permission_repo.py",
        "app/pms/system/service_auth/services/__init__.py",
        "app/pms/system/service_auth/services/pms_service_permission_service.py",
        "app/pms/system/service_auth/deps/__init__.py",
        "app/pms/system/service_auth/deps/pms_service_permission_deps.py",
    }

    missing = [
        file_path
        for file_path in sorted(expected_files)
        if not (ROOT / file_path).is_file()
    ]

    assert missing == []


def test_pms_code_does_not_import_global_service_auth_package() -> None:
    violations: list[str] = []
    current_file = Path(__file__).resolve()

    for directory in ("app", "tests", "alembic", "scripts"):
        root = ROOT / directory
        if not root.exists():
            continue

        for path in sorted(root.rglob("*.py")):
            if path.resolve() == current_file:
                continue

            text = path.read_text(encoding="utf-8")
            if "from app.service_auth" in text or "import app.service_auth" in text:
                violations.append(path.relative_to(ROOT).as_posix())

    assert violations == []


def test_pms_metadata_loads_pms_scoped_service_auth_models() -> None:
    text = (ROOT / "app/db/metadata.py").read_text(encoding="utf-8")

    assert "import app.pms.system.service_auth.models" in text
    assert "import app.service_auth.models" not in text

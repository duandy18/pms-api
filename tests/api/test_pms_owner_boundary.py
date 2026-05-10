# tests/api/test_pms_owner_boundary.py
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_IMPORT_RE = re.compile(
    r"^\s*(from|import)\s+app\.(wms|oms|procurement|finance|shipping_assist)\b"
)


def test_pms_owner_runtime_does_not_import_non_pms_business_domains() -> None:
    violations: list[str] = []

    for path in sorted((ROOT / "app" / "pms").rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if FORBIDDEN_IMPORT_RE.search(line):
                violations.append(f"{rel}:{line_no}: {line.strip()}")

    assert violations == []

# tests/api/test_pms_supplier_projection_feed_contract.py
from __future__ import annotations

from app.main import app


def _method_paths() -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", None) or []
        for method in methods:
            if method in {"GET", "POST", "PATCH", "PUT", "DELETE"}:
                pairs.add((method, path))
    return pairs


def test_supplier_projection_feed_route_is_mounted() -> None:
    assert ("GET", "/pms/read/v1/projection-feed/suppliers") in _method_paths()


def test_supplier_projection_feed_openapi_model_is_stable() -> None:
    schema = app.openapi()

    response_schema = schema["paths"]["/pms/read/v1/projection-feed/suppliers"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]

    assert response_schema["$ref"] == "#/components/schemas/PmsProjectionSupplierFeedOut"

    components = schema["components"]["schemas"]
    out_schema = components["PmsProjectionSupplierFeedOut"]
    row_schema = components["PmsProjectionSupplierFeedRow"]

    assert out_schema["properties"]["rows"]["items"]["$ref"] == (
        "#/components/schemas/PmsProjectionSupplierFeedRow"
    )
    assert {
        "supplier_id",
        "supplier_code",
        "supplier_name",
        "active",
        "website",
        "source_updated_at",
    } <= set(row_schema["properties"])

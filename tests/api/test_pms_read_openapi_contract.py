# tests/api/test_pms_read_openapi_contract.py
from __future__ import annotations

from typing import Any

from app.main import app


def _schema() -> dict[str, Any]:
    return app.openapi()


def _response_schema(schema: dict[str, Any], path: str, method: str) -> dict[str, Any]:
    response = schema["paths"][path][method]["responses"]["200"]
    return response["content"]["application/json"]["schema"]


def _response_ref(schema: dict[str, Any], path: str, method: str) -> str:
    return _response_schema(schema, path, method)["$ref"]


def _array_item_ref(schema: dict[str, Any], path: str, method: str) -> str:
    return _response_schema(schema, path, method)["items"]["$ref"]


def _request_ref(schema: dict[str, Any], path: str, method: str) -> str:
    request_body = schema["paths"][path][method]["requestBody"]
    return request_body["content"]["application/json"]["schema"]["$ref"]


def test_pms_read_v1_paths_and_methods_are_stable() -> None:
    schema = _schema()

    expected = {
        "/pms/read/v1/health": {"get"},
        "/pms/read/v1/projection-feed/items": {"get"},
        "/pms/read/v1/projection-feed/uoms": {"get"},
        "/pms/read/v1/projection-feed/sku-codes": {"get"},
        "/pms/read/v1/projection-feed/barcodes": {"get"},
        "/pms/read/v1/items/basic": {"get"},
        "/pms/read/v1/items/basic/{item_id}": {"get"},
        "/pms/read/v1/items/basic/batch": {"post"},
        "/pms/read/v1/items/policy-by-sku": {"get"},
        "/pms/read/v1/items/{item_id}/policy": {"get"},
        "/pms/read/v1/items/policies/batch": {"post"},
        "/pms/read/v1/items/report-search": {"get"},
        "/pms/read/v1/items/report-meta/batch": {"post"},
        "/pms/read/v1/items/{item_id}/uoms": {"get"},
        "/pms/read/v1/uoms/{item_uom_id}": {"get"},
        "/pms/read/v1/uoms/query": {"post"},
        "/pms/read/v1/items/uom-defaults/batch": {"post"},
        "/pms/read/v1/barcodes/{barcode_id}": {"get"},
        "/pms/read/v1/items/{item_id}/barcodes": {"get"},
        "/pms/read/v1/barcodes/query": {"post"},
        "/pms/read/v1/barcodes/probe": {"post"},
        "/pms/read/v1/sku-codes/resolve-outbound-default": {"get"},
        "/pms/read/v1/sku-codes/{sku_code_id}": {"get"},
        "/pms/read/v1/items/{item_id}/sku-codes": {"get"},
        "/pms/read/v1/sku-codes/query": {"post"},
    }

    actual = {
        path: set(methods.keys())
        for path, methods in schema["paths"].items()
        if path.startswith("/pms/read/v1")
    }

    assert actual == expected


def test_pms_read_v1_request_response_models_are_stable() -> None:
    schema = _schema()

    assert _response_ref(schema, "/pms/read/v1/health", "get") == (
        "#/components/schemas/PmsReadHealthOut"
    )
    assert _response_ref(schema, "/pms/read/v1/projection-feed/items", "get") == (
        "#/components/schemas/PmsProjectionItemFeedOut"
    )
    assert _response_ref(schema, "/pms/read/v1/projection-feed/uoms", "get") == (
        "#/components/schemas/PmsProjectionUomFeedOut"
    )
    assert _response_ref(schema, "/pms/read/v1/projection-feed/sku-codes", "get") == (
        "#/components/schemas/PmsProjectionSkuCodeFeedOut"
    )
    assert _response_ref(schema, "/pms/read/v1/projection-feed/barcodes", "get") == (
        "#/components/schemas/PmsProjectionBarcodeFeedOut"
    )

    assert _array_item_ref(schema, "/pms/read/v1/items/basic", "get") == (
        "#/components/schemas/ItemBasic"
    )
    assert _response_ref(schema, "/pms/read/v1/items/basic/{item_id}", "get") == (
        "#/components/schemas/ItemBasic"
    )
    assert _request_ref(schema, "/pms/read/v1/items/basic/batch", "post") == (
        "#/components/schemas/ItemIdsBatchIn"
    )
    assert _response_ref(schema, "/pms/read/v1/items/basic/batch", "post") == (
        "#/components/schemas/ItemBasicBatchOut"
    )

    assert _response_ref(schema, "/pms/read/v1/items/policy-by-sku", "get") == (
        "#/components/schemas/ItemPolicy"
    )
    assert _response_ref(schema, "/pms/read/v1/items/{item_id}/policy", "get") == (
        "#/components/schemas/ItemPolicy"
    )
    assert _request_ref(schema, "/pms/read/v1/items/policies/batch", "post") == (
        "#/components/schemas/ItemIdsBatchIn"
    )
    assert _response_ref(schema, "/pms/read/v1/items/policies/batch", "post") == (
        "#/components/schemas/ItemPolicyBatchOut"
    )

    assert _response_ref(schema, "/pms/read/v1/items/report-search", "get") == (
        "#/components/schemas/ReportSearchOut"
    )
    assert _request_ref(schema, "/pms/read/v1/items/report-meta/batch", "post") == (
        "#/components/schemas/ItemIdsBatchIn"
    )
    assert _response_ref(schema, "/pms/read/v1/items/report-meta/batch", "post") == (
        "#/components/schemas/ItemReportMetaBatchOut"
    )

    assert _array_item_ref(schema, "/pms/read/v1/items/{item_id}/uoms", "get") == (
        "#/components/schemas/PmsExportUom"
    )
    assert _response_ref(schema, "/pms/read/v1/uoms/{item_uom_id}", "get") == (
        "#/components/schemas/PmsExportUom"
    )
    assert _request_ref(schema, "/pms/read/v1/uoms/query", "post") == (
        "#/components/schemas/UomQueryIn"
    )
    assert _response_ref(schema, "/pms/read/v1/uoms/query", "post") == (
        "#/components/schemas/UomQueryOut"
    )
    assert _request_ref(schema, "/pms/read/v1/items/uom-defaults/batch", "post") == (
        "#/components/schemas/UomDefaultsBatchIn"
    )
    assert _response_ref(schema, "/pms/read/v1/items/uom-defaults/batch", "post") == (
        "#/components/schemas/UomDefaultsBatchOut"
    )

    assert _response_ref(schema, "/pms/read/v1/barcodes/{barcode_id}", "get") == (
        "#/components/schemas/PmsExportBarcode"
    )
    assert _array_item_ref(schema, "/pms/read/v1/items/{item_id}/barcodes", "get") == (
        "#/components/schemas/PmsExportBarcode"
    )
    assert _request_ref(schema, "/pms/read/v1/barcodes/query", "post") == (
        "#/components/schemas/BarcodeQueryIn"
    )
    assert _response_ref(schema, "/pms/read/v1/barcodes/query", "post") == (
        "#/components/schemas/BarcodeQueryOut"
    )
    assert _request_ref(schema, "/pms/read/v1/barcodes/probe", "post") == (
        "#/components/schemas/BarcodeProbeIn"
    )
    assert _response_ref(schema, "/pms/read/v1/barcodes/probe", "post") == (
        "#/components/schemas/BarcodeProbeOut"
    )

    assert _response_ref(schema, "/pms/read/v1/sku-codes/resolve-outbound-default", "get") == (
        "#/components/schemas/PmsExportSkuCodeResolution"
    )
    assert _response_ref(schema, "/pms/read/v1/sku-codes/{sku_code_id}", "get") == (
        "#/components/schemas/PmsExportSkuCode"
    )
    assert _array_item_ref(schema, "/pms/read/v1/items/{item_id}/sku-codes", "get") == (
        "#/components/schemas/PmsExportSkuCode"
    )
    assert _request_ref(schema, "/pms/read/v1/sku-codes/query", "post") == (
        "#/components/schemas/SkuCodeQueryIn"
    )
    assert _response_ref(schema, "/pms/read/v1/sku-codes/query", "post") == (
        "#/components/schemas/SkuCodeQueryOut"
    )

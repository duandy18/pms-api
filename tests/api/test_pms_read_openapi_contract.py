# tests/api/test_pms_read_openapi_contract.py
from __future__ import annotations

from typing import Any

from app.main import app


def _schema() -> dict[str, Any]:
    return app.openapi()


def _response_ref(schema: dict[str, Any], path: str, method: str, status_code: str = "200") -> str:
    response = schema["paths"][path][method]["responses"][status_code]
    return response["content"]["application/json"]["schema"]["$ref"]


def _request_ref(schema: dict[str, Any], path: str, method: str) -> str:
    request_body = schema["paths"][path][method]["requestBody"]
    return request_body["content"]["application/json"]["schema"]["$ref"]


def test_pms_read_v1_paths_and_methods_are_stable() -> None:
    schema = _schema()

    expected = {
        "/pms/read/v1/health": {"get"},
        "/pms/read/v1/items/basic/batch": {"post"},
        "/pms/read/v1/items/policies/batch": {"post"},
        "/pms/read/v1/items/report-search": {"get"},
        "/pms/read/v1/items/report-meta/batch": {"post"},
        "/pms/read/v1/uoms/query": {"post"},
        "/pms/read/v1/items/uom-defaults/batch": {"post"},
        "/pms/read/v1/barcodes/query": {"post"},
        "/pms/read/v1/barcodes/probe": {"post"},
        "/pms/read/v1/sku-codes/query": {"post"},
        "/pms/read/v1/sku-codes/resolve-outbound-default": {"get"},
    }

    actual = {
        path: set(methods.keys())
        for path, methods in schema["paths"].items()
        if path.startswith("/pms/read/v1")
    }

    assert actual == expected


def test_pms_read_v1_request_response_models_are_stable() -> None:
    schema = _schema()

    expected_refs = {
        ("/pms/read/v1/health", "get"): (None, "#/components/schemas/PmsReadHealthOut"),
        (
            "/pms/read/v1/items/basic/batch",
            "post",
        ): ("#/components/schemas/ItemIdsBatchIn", "#/components/schemas/ItemBasicBatchOut"),
        (
            "/pms/read/v1/items/policies/batch",
            "post",
        ): ("#/components/schemas/ItemIdsBatchIn", "#/components/schemas/ItemPolicyBatchOut"),
        (
            "/pms/read/v1/items/report-meta/batch",
            "post",
        ): ("#/components/schemas/ItemIdsBatchIn", "#/components/schemas/ItemReportMetaBatchOut"),
        (
            "/pms/read/v1/uoms/query",
            "post",
        ): ("#/components/schemas/UomQueryIn", "#/components/schemas/UomQueryOut"),
        (
            "/pms/read/v1/items/uom-defaults/batch",
            "post",
        ): ("#/components/schemas/UomDefaultsBatchIn", "#/components/schemas/UomDefaultsBatchOut"),
        (
            "/pms/read/v1/barcodes/query",
            "post",
        ): ("#/components/schemas/BarcodeQueryIn", "#/components/schemas/BarcodeQueryOut"),
        (
            "/pms/read/v1/barcodes/probe",
            "post",
        ): ("#/components/schemas/BarcodeProbeIn", "#/components/schemas/BarcodeProbeOut"),
        (
            "/pms/read/v1/sku-codes/query",
            "post",
        ): ("#/components/schemas/SkuCodeQueryIn", "#/components/schemas/SkuCodeQueryOut"),
        (
            "/pms/read/v1/sku-codes/resolve-outbound-default",
            "get",
        ): (None, "#/components/schemas/PmsExportSkuCodeResolution"),
    }

    for (path, method), (request_ref, response_ref) in expected_refs.items():
        if request_ref is not None:
            assert _request_ref(schema, path, method) == request_ref
        assert _response_ref(schema, path, method) == response_ref


def test_pms_read_v1_report_search_query_contract_is_stable() -> None:
    schema = _schema()

    operation = schema["paths"]["/pms/read/v1/items/report-search"]["get"]
    params = {param["name"]: param for param in operation["parameters"]}

    assert set(params) == {"keyword", "limit"}
    assert params["keyword"]["required"] is True
    assert params["keyword"]["schema"]["minLength"] == 1
    assert params["keyword"]["schema"]["maxLength"] == 128

    assert params["limit"]["required"] is False
    assert params["limit"]["schema"]["default"] == 50
    assert params["limit"]["schema"]["minimum"] == 1
    assert params["limit"]["schema"]["maximum"] == 500

    assert _response_ref(schema, "/pms/read/v1/items/report-search", "get") == (
        "#/components/schemas/ReportSearchOut"
    )


def test_pms_read_v1_resolve_outbound_default_query_contract_is_stable() -> None:
    schema = _schema()

    operation = schema["paths"]["/pms/read/v1/sku-codes/resolve-outbound-default"]["get"]
    params = {param["name"]: param for param in operation["parameters"]}

    assert set(params) == {"code", "enabled_only"}
    assert params["code"]["required"] is True
    assert params["code"]["schema"]["minLength"] == 1
    assert params["code"]["schema"]["maxLength"] == 128

    assert params["enabled_only"]["required"] is False
    assert params["enabled_only"]["schema"]["default"] is True

    assert _response_ref(schema, "/pms/read/v1/sku-codes/resolve-outbound-default", "get") == (
        "#/components/schemas/PmsExportSkuCodeResolution"
    )


def test_pms_read_v1_component_schemas_are_present() -> None:
    schema = _schema()
    components = set(schema["components"]["schemas"])

    expected_components = {
        "BarcodeProbeError",
        "BarcodeProbeIn",
        "BarcodeProbeOut",
        "BarcodeProbeStatus",
        "BarcodeQueryIn",
        "BarcodeQueryOut",
        "ItemBasic",
        "ItemBasicBatchOut",
        "ItemIdsBatchIn",
        "ItemPolicy",
        "ItemPolicyBatchOut",
        "ItemReportMeta",
        "ItemReportMetaBatchOut",
        "PmsExportBarcode",
        "PmsExportSkuCode",
        "PmsExportSkuCodeResolution",
        "PmsExportUom",
        "PmsReadError",
        "PmsReadHealthOut",
        "ReportSearchOut",
        "SkuCodeQueryIn",
        "SkuCodeQueryOut",
        "UomDefaultsBatchIn",
        "UomDefaultsBatchOut",
        "UomQueryIn",
        "UomQueryOut",
    }

    assert expected_components <= components

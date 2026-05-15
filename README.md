# pms-api

Standalone PMS API service.

Current goal:

- PMS API is an independent backend process.
- PMS owns product master data such as items, UOMs, barcodes, SKU codes, suppliers, categories, brands, and attributes.
- WMS / OMS / Procurement / Finance consume PMS through explicit API contracts.
- Downstream systems must not read PMS owner tables directly.

## Local dev ports

| Component | Port | Purpose |
| --- | ---: | --- |
| pms-api | 8005 | FastAPI / Uvicorn HTTP service |
| pms-web | 5174 | Vite dev server |
| pms-db | 5433 | Shared local PostgreSQL host port |

See `docs/dev-ports.md` for the full local port contract.

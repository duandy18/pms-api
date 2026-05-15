# PMS local development ports

## Port contract

| Component | Port | Purpose |
| --- | ---: | --- |
| pms-api | 8005 | FastAPI / Uvicorn HTTP service |
| pms-web | 5174 | Vite dev server |
| pms-db | 5433 | Shared local PostgreSQL host port |

## Environment variables

| Variable | Example | Meaning |
| --- | --- | --- |
| `PMS_DATABASE_URL` | `postgresql+psycopg://pms:pms@127.0.0.1:5433/pms` | PMS development database |

## Rules

- Local development PostgreSQL uses the shared host port `5433`.
- PMS uses its own database role: `pms:pms`.
- Do not use `5433` for FastAPI. It is reserved for PostgreSQL.
- Do not use `8005` for PostgreSQL. It is reserved for pms-api HTTP.
- pms-web should call pms-api through `VITE_API_BASE_URL=http://127.0.0.1:8005`.

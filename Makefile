SHELL := /bin/bash
.RECIPEPREFIX := >

VENV  := .venv
PY    := $(VENV)/bin/python
PIP   := $(VENV)/bin/pip
PYTEST:= $(VENV)/bin/pytest
ALEMB := $(PY) -m alembic

DEV_DB_DSN := postgresql+psycopg://wms:wms@127.0.0.1:5433/pms

HOST ?= 0.0.0.0
PORT ?= 8005

.PHONY: venv install uvicorn dev dev-db test lint routes db-smoke upgrade-dev alembic-check alembic-current alembic-history dev-ensure-admin

venv:
>python3 -m venv $(VENV)
>$(PIP) install -U pip

install:
>$(PIP) install -e ".[dev]"

uvicorn:
>PMS_DATABASE_URL="$(DEV_DB_DSN)" PYTHONPATH=. $(PY) -m uvicorn app.main:app --host $(HOST) --port $(PORT) --reload

dev: uvicorn

dev-db: uvicorn

test:
>PYTHONPATH=. $(PYTEST) $(TESTS)

lint:
>$(VENV)/bin/ruff check app tests

routes:
>PYTHONPATH=. $(PY) scripts/print_routes.py

db-smoke:
>PMS_DATABASE_URL="$(DEV_DB_DSN)" PYTHONPATH=. $(PY) scripts/db_smoke.py

upgrade-dev:
>PMS_DATABASE_URL="$(DEV_DB_DSN)" PYTHONPATH=. $(ALEMB) upgrade head

alembic-check:
>PMS_DATABASE_URL="$(DEV_DB_DSN)" PYTHONPATH=. $(ALEMB) check

alembic-current:
>PMS_DATABASE_URL="$(DEV_DB_DSN)" PYTHONPATH=. $(ALEMB) current

alembic-history:
>PMS_DATABASE_URL="$(DEV_DB_DSN)" PYTHONPATH=. $(ALEMB) history

dev-ensure-admin:
>PMS_DATABASE_URL="$(DEV_DB_DSN)" PYTHONPATH=. $(PY) scripts/ensure_admin.py

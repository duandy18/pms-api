SHELL := /bin/bash
VENV  := .venv
PY    := $(VENV)/bin/python
PIP   := $(VENV)/bin/pip
PYTEST:= $(VENV)/bin/pytest
DEV_DB_DSN := postgresql+psycopg://wms:wms@127.0.0.1:5433/wms

.PHONY: venv install dev dev-db test lint routes db-smoke

venv:
	python3 -m venv $(VENV)
	$(PIP) install -U pip

install:
	$(PIP) install -e ".[dev]"

dev:
	PYTHONPATH=. $(PY) -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload

dev-db:
	PMS_DATABASE_URL="$(DEV_DB_DSN)" PYTHONPATH=. $(PY) -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

test:
	PYTHONPATH=. $(PYTEST) $(TESTS)

lint:
	$(VENV)/bin/ruff check app tests

routes:
	PYTHONPATH=. $(PY) scripts/print_routes.py

db-smoke:
	PMS_DATABASE_URL="$(DEV_DB_DSN)" PYTHONPATH=. $(PY) scripts/db_smoke.py

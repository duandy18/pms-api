SHELL := /bin/bash
VENV  := .venv
PY    := $(VENV)/bin/python
PIP   := $(VENV)/bin/pip
PYTEST:= $(VENV)/bin/pytest

.PHONY: venv install dev test lint routes

venv:
	python3 -m venv $(VENV)
	$(PIP) install -U pip

install:
	$(PIP) install -e ".[dev]"

dev:
	PYTHONPATH=. $(PY) -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload

test:
	PYTHONPATH=. $(PYTEST) $(TESTS)

lint:
	$(VENV)/bin/ruff check app tests

routes:
	PYTHONPATH=. $(PY) scripts/print_routes.py

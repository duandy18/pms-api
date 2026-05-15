SHELL := /bin/bash
.RECIPEPREFIX := >

VENV ?= .venv
PY ?= $(shell if [ -x "$(VENV)/bin/python3" ]; then echo "$(VENV)/bin/python3"; elif [ -x "$(VENV)/bin/python" ]; then echo "$(VENV)/bin/python"; else echo "python3"; fi)
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
ALEMB := $(PY) -m alembic

DEV_DB_DSN ?= postgresql+psycopg://pms:pms@127.0.0.1:5433/pms
PMS_DATABASE_URL ?= $(DEV_DB_DSN)

HOST ?= 0.0.0.0
PORT ?= 8005

# Local private environment overrides.
# .env.local must not be committed.
ifneq (,$(wildcard .env.local))
include .env.local
endif

DEV_ENV := PMS_DATABASE_URL="$(PMS_DATABASE_URL)" PYTHONPATH=.

.PHONY: help
.PHONY: env env-dev env-check
.PHONY: venv install uvicorn dev dev-db test lint routes db-smoke upgrade-dev alembic-check alembic-current alembic-history dev-ensure-admin

help:
> @echo "PMS API 常用命令："
> @echo ""
> @echo "  make env                         打印当前本地开发环境变量"
> @echo "  make env-check                   检查 PMS 本地环境"
> @echo "  make uvicorn                     启动本地后端，默认端口 8005"
> @echo "  make upgrade-dev                 开发库迁移到 head"
> @echo "  make alembic-check               检查开发库 Alembic 是否与模型一致"
> @echo "  make dev-ensure-admin            初始化 / 修复本地 admin"
> @echo "  make test TESTS=tests/xxx.py     跑指定测试"
> @echo "  make lint                        ruff check app tests"
> @echo "  make routes                      打印路由"
> @echo "  make db-smoke                    检查数据库连接"

env: env-dev

env-dev:
> @printf '%s\n' 'export PMS_DATABASE_URL="$(PMS_DATABASE_URL)"'
> @printf '%s\n' 'export PYTHONPATH=.'

env-check:
> @echo "===== PMS API env ====="
> @echo "PY=$(PY)"
> @echo "HOST=$(HOST)"
> @echo "PORT=$(PORT)"
> @echo "PMS_DATABASE_URL=$(PMS_DATABASE_URL)"
> @echo
> @echo "===== PMS env import check ====="
> @$(DEV_ENV) $(PY) -c "import os; assert os.getenv('PMS_DATABASE_URL'), 'PMS_DATABASE_URL is required'; from app.main import app; print('PMS app import OK:', len(app.routes), 'routes')"

venv:
> python3 -m venv $(VENV)
> $(PIP) install -U pip

install:
> $(PIP) install -e ".[dev]"

uvicorn:
> $(DEV_ENV) $(PY) -m uvicorn app.main:app --host $(HOST) --port $(PORT) --reload

dev: uvicorn

dev-db: uvicorn

test:
> $(DEV_ENV) $(PYTEST) $(TESTS)

lint:
> $(VENV)/bin/ruff check app tests

routes:
> $(DEV_ENV) $(PY) scripts/print_routes.py

db-smoke:
> $(DEV_ENV) $(PY) scripts/db_smoke.py

upgrade-dev:
> $(DEV_ENV) $(ALEMB) upgrade head

alembic-check:
> $(DEV_ENV) $(ALEMB) check

alembic-current:
> $(DEV_ENV) $(ALEMB) current

alembic-history:
> $(DEV_ENV) $(ALEMB) history

dev-ensure-admin:
> $(DEV_ENV) $(PY) scripts/ensure_admin.py

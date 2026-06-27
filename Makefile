# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI Contact Center — Makefile
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

.PHONY: dev stop logs test-unit test-integration lint fmt seed tables

# ── Local Development ─────────────────────────────────
dev:
	docker compose up --build -d

stop:
	docker compose down

logs:
	docker compose logs -f api

# ── Database ──────────────────────────────────────────
tables:
	docker compose exec api python -m app.core.dynamo_init

# ── Knowledge Base ────────────────────────────────────
seed:
	pip install httpx beautifulsoup4 && python knowledge_base/scripts/seed.py

ingest:
	docker compose exec api python -m app.pipeline.ingestion --seed

# ── Testing ───────────────────────────────────────────
test-unit:
	cd backend && python -m pytest tests/unit/ -v --cov=app --cov-report=term-missing

test-integration:
	cd backend && python -m pytest tests/integration/ -v

# ── Code Quality ──────────────────────────────────────
lint:
	cd backend && ruff check . && mypy app/

fmt:
	cd backend && ruff format .

# ── Pre-commit ────────────────────────────────────────
hooks:
	pip install pre-commit && pre-commit install

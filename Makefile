.PHONY: dev stop migrate-local test lint format build push tf-plan-staging tf-apply-staging tf-plan-prod

# ── Local Dev ─────────────────────────────────────────────────────────────────
dev:
	docker compose up --build

stop:
	docker compose down -v

migrate-local:
	docker compose exec api python -m app.core.dynamo_init

# ── Testing ───────────────────────────────────────────────────────────────────
test:
	docker compose exec api pytest tests/ -v --tb=short

test-unit:
	docker compose exec api pytest tests/unit/ -v

test-integration:
	docker compose exec api pytest tests/integration/ -v

test-cov:
	docker compose exec api pytest tests/ --cov=app --cov-report=xml --cov-report=term-missing

# ── Linting ───────────────────────────────────────────────────────────────────
lint:
	cd backend && ruff check . && mypy app/ --ignore-missing-imports

format:
	cd backend && ruff format .

# ── Docker ────────────────────────────────────────────────────────────────────
build:
	docker build -f infrastructure/docker/Dockerfile.api -t kms-api:latest ./backend
	docker build -f infrastructure/docker/Dockerfile.frontend -t kms-frontend:latest ./frontend

# ── Terraform Staging ─────────────────────────────────────────────────────────
tf-init-staging:
	cd infrastructure/terraform/environments/staging && terraform init

tf-plan-staging:
	cd infrastructure/terraform/environments/staging && terraform plan -var-file=terraform.tfvars

tf-apply-staging:
	cd infrastructure/terraform/environments/staging && terraform apply -var-file=terraform.tfvars

tf-destroy-staging:
	cd infrastructure/terraform/environments/staging && terraform destroy -var-file=terraform.tfvars

# ── Terraform Prod ────────────────────────────────────────────────────────────
tf-init-prod:
	cd infrastructure/terraform/environments/prod && terraform init

tf-plan-prod:
	cd infrastructure/terraform/environments/prod && terraform plan -var-file=terraform.tfvars

tf-apply-prod:
	cd infrastructure/terraform/environments/prod && terraform apply -var-file=terraform.tfvars

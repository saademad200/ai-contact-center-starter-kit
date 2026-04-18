# Banking KMS — Internal Knowledge Management System

> **Status: Planning & Scaffolding Phase** — Implementation in progress. See [`PROJECT_PLAN.md`](PROJECT_PLAN.md) for the complete technical specification.

An internal RAG-based chat system for a banking-domain software company. Employees ask plain-English questions and get accurate, sourced answers drawn from SBP regulatory documents and bank reference material.

---

## What's in this repo right now

| Path | What it is |
|------|-----------|
| [`PROJECT_PLAN.md`](PROJECT_PLAN.md) | Complete team spec — architecture, data models, API contracts, sequence diagrams, CI/CD guide, Terraform guide |
| [`docker-compose.yml`](docker-compose.yml) | Local dev: FastAPI + Next.js + ChromaDB + DynamoDB Local |
| [`.env.example`](.env.example) | All environment variables documented with examples |
| [`Makefile`](Makefile) | Developer shortcuts (`make dev`, `make test`, `make lint`, etc.) |
| [`.pre-commit-config.yaml`](.pre-commit-config.yaml) | Code quality hooks: ruff, mypy, bandit, detect-secrets, hadolint |
| [`backend/`](backend/) | FastAPI app — directory structure + stub files with specs |
| [`backend/requirements.txt`](backend/requirements.txt) | All Python dependencies (pinned) |
| [`backend/pyproject.toml`](backend/pyproject.toml) | ruff, mypy, bandit, pytest configuration |
| [`.github/workflows/`](.github/workflows/) | GitHub Actions: `ci.yml`, `staging.yml`, `prod.yml`, `terraform.yml` |
| [`knowledge_base/`](knowledge_base/) | Seed script to download SBP + HBL public documents |
| [`infrastructure/terraform/`](infrastructure/terraform/) | Terraform directory structure (see PROJECT_PLAN.md for build guide) |

**Not yet implemented:** backend logic, frontend, Terraform `.tf` files, Dockerfiles.

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Backend | FastAPI (Python 3.11) |
| Frontend | Next.js 14 (planned) |
| Vector store | ChromaDB |
| Metadata DB | AWS DynamoDB |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (free, local) |
| LLM | Groq API — Llama 3.1 70B (free tier) / HuggingFace |
| Infrastructure | AWS ECS Fargate + Terraform |
| CI/CD | GitHub Actions |

---

## Quick Start (local dev)

```bash
# 1. Copy environment file and fill in your keys
cp .env.example .env

# 2. Install pre-commit hooks
pip install pre-commit && pre-commit install

# 3. Start all services
make dev
# API:       http://localhost:8000/docs
# DynamoDB admin: http://localhost:8888

# 4. Create local DynamoDB tables
make migrate-local

# 5. Download knowledge base documents (SBP regulations + HBL annual reports)
pip install httpx
python knowledge_base/scripts/seed_knowledge_base.py
```

---

## Knowledge Base

The seed script downloads **20 publicly available documents** from authoritative sources:

- **13 SBP documents** — Prudential Regulations (SME, Consumer, Microfinance, Housing, Agriculture), AML/CFT guidelines, core banking laws
- **7 HBL documents** — Annual reports 2021–2024, quarterly reports 2024

```bash
python knowledge_base/scripts/seed_knowledge_base.py          # all 20 docs
python knowledge_base/scripts/seed_knowledge_base.py --category sbp   # SBP only
python knowledge_base/scripts/seed_knowledge_base.py --category hbl   # HBL only
python knowledge_base/scripts/seed_knowledge_base.py --dry-run        # preview
```

> Raw PDFs are gitignored — each developer runs the script locally.

---

## CI/CD Workflows

| File | Trigger | What it does |
|------|---------|-------------|
| `ci.yml` | Every push | pre-commit + unit tests + coverage |
| `staging.yml` | Push to `staging` | Build → ECR → deploy ECS staging |
| `prod.yml` | Push to `main` | Manual approval → build → ECR → deploy ECS prod → Slack |
| `terraform.yml` | Push to `infrastructure` | fmt + validate + plan → comment on PR → manual apply |

---

## Required GitHub Secrets

```
AWS_ACCOUNT_ID      — Your AWS account ID
STAGING_URL         — https://<staging-alb-dns>
PROD_URL            — https://<prod-alb-dns>
SLACK_WEBHOOK_URL   — For prod deploy notifications
```

---

## Project Plan

See **[`PROJECT_PLAN.md`](PROJECT_PLAN.md)** for the full specification including:
- Architecture diagrams
- DynamoDB table schemas (all fields + GSIs)
- Complete API contract with request/response examples
- Python service interfaces (method signatures)
- Sequence diagrams for core flows
- Terraform build guide (S3 state, DynamoDB locking, module structure, separate tfvars)
- GitHub Actions walkthrough
- Local dev & deployment guide

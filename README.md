# AI Contact Centre — Al Meezan Investments

> AI-powered customer support agent for Al Meezan Investments, Pakistan's largest Shariah-compliant asset management company. Uses **tool calling** (not just RAG) to answer fund queries, compare funds, assess risk profiles, and escalate to human agents.

## Architecture

| Component | Technology |
|-----------|-----------|
| API + Agent | FastAPI, Groq (Llama 3.1 70B), WebSocket |
| Chat Widget | Vanilla JS (embeddable `<script>` tag) |
| Admin Panel | FastAPI + Jinja2 templates |
| Vector Store | ChromaDB |
| Database | DynamoDB (PAY_PER_REQUEST) |
| Embeddings | sentence-transformers (local, 384d) |
| Infrastructure | Terraform (ECS Fargate), GitHub Actions CI/CD |

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env: set GROQ_API_KEY + ADMIN_PASSWORD

# 2. Start services
make dev
# API:            http://localhost:8000
# API Docs:       http://localhost:8000/docs
# Admin Panel:    http://localhost:8000/admin
# Chat Widget:    http://localhost:8000/static/widget.html
# Demo Page:      http://localhost:8000/static/demo.html
# DynamoDB Admin: http://localhost:8888

# 3. Create tables + seed
make tables
make seed
make ingest

# 4. Run tests
make test-unit
make lint
```

## AI Agent Tools

The agent uses **Groq tool calling** to invoke the right function based on customer intent:

| Tool | Purpose |
|------|---------|
| `search_knowledge_base` | RAG search for FAQs, processes, regulations |
| `get_fund_nav` | Current NAV lookup from MUFAP data |
| `get_fund_performance` | Fund return metrics (YTD, 1Y, 3Y, 5Y) |
| `compare_funds` | Side-by-side fund comparison |
| `assess_risk_profile` | Guided risk assessment → fund allocation |
| `escalate_to_human` | Create support ticket for human agent |

## Documentation

- [`PROJECT_PLAN.md`](PROJECT_PLAN.md) — Complete technical specification
- [`TASK_DISTRIBUTION.md`](TASK_DISTRIBUTION.md) — Team task assignment + sprint plan

## Current State

🏗️ **Scaffolded** — All directories, stubs, and interfaces defined. Ready for modular implementation per `TASK_DISTRIBUTION.md`.

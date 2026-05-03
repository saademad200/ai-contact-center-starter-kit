# AI Contact Centre — Alfalah Investments

> AI-powered customer support agent for Alfalah Investments. Uses **OpenAI tool calling**, **Automated Fine-Tuning**, and **Live Web Scraping** to answer fund queries, compare funds, and provide accurate, up-to-date conversational support.

## Architecture

| Component | Technology |
|-----------|-----------|
| API + Agent | FastAPI, OpenAI (`gpt-4o-mini`), WebSocket |
| Tool Calling Data | Live Web Scraping (BeautifulSoup4) |
| Observability | Langfuse (Tracing & Evals) |
| Fine-Tuning Pipeline| AWS S3 → AWS Lambda (Text cleaner) → OpenAI FT Job |
| Chat Widget | Vanilla JS (embeddable `<script>` tag) |
| Admin Panel | FastAPI + Jinja2 templates |
| Vector Store | ChromaDB |
| Database | DynamoDB (Registries & Conversations) |
| Infrastructure | Terraform (ECS Fargate + CodeDeploy Blue/Green), GitHub Actions |

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env: set OPENAI_API_KEY, LANGFUSE keys, etc.

# 2. Start services
make dev
# API:            http://localhost:8000
# API Docs:       http://localhost:8000/docs
# Admin Panel:    http://localhost:8000/admin
# Chat Widget:    http://localhost:8000/static/widget.js
# Demo Page:      http://localhost:8000/demo

# 3. Create tables + seed
make tables
make seed
make ingest

# 4. Run tests
make test-unit
make lint
```

## AI Agent Tools

The agent uses **OpenAI tool calling** to invoke the right function based on customer intent:

| Tool | Purpose |
|------|---------|
| `search_knowledge_base` | RAG search for PDFs, prospectuses, regulations |
| `get_fund_nav` | Live web scraping for current NAV |
| `get_fund_performance` | Live web scraping for fund return metrics |
| `compare_funds` | Side-by-side fund comparison from live data |
| `escalate_to_human` | (Optional) Create support ticket for human agent via SES |

## Documentation

- [`PROJECT_PLAN.md`](PROJECT_PLAN.md) — Complete technical specification
- [`TASK_DISTRIBUTION.md`](TASK_DISTRIBUTION.md) — Team task assignment + sprint plan
- [`docs/INFRASTRUCTURE_CHECKLIST.md`](docs/INFRASTRUCTURE_CHECKLIST.md) — Infrastructure deployment checklist

## Current State

✅ **Complete** — All components (Infrastructure, Agent, API, Widget, Admin) are fully implemented.
- **Frontend** (`frontend/`) contains the independent Nginx-hosted landing page and vanilla JS chat widget, built as a standalone ECS service.
- **Backend** (`backend/`) contains the FastAPI server which handles the API, Agent WebSockets, and **server-side renders the Admin Panel** using Jinja2 templates at the `/admin` path. This is deployed as its own ECS service.
- **Infrastructure** runs via GitFlow-aware GitHub Actions using Terraform and AWS CodeDeploy (Blue/Green).

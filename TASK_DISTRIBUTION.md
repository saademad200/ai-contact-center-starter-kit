# Task Distribution — 5 Team Members

> Reference: [`PROJECT_PLAN.md`](PROJECT_PLAN.md) for all specs, schemas, and interfaces.

---

## Person 1 — DevOps / Infrastructure
**Focus:** Terraform, CI/CD, Docker, code quality tooling

| Task | Plan Reference | Priority |
|------|---------------|----------|
| Write all Terraform modules (`vpc`, `ecs`, `dynamodb`, `s3`, `iam`) | §11 | P0 |
| Configure S3 remote state + DynamoDB lock table | §11 (bootstrap) | P0 |
| Create `staging/` and `prod/` environment configs with separate `.tfvars` | §11 | P0 |
| Write `Dockerfile.api` (multi-stage, Python 3.11-slim) | §10 | P0 |
| Write `Dockerfile.widget` (nginx alpine, static files) | §10 | P1 |
| Implement all 4 GitHub Actions workflows (`ci`, `staging`, `prod`, `terraform`) | §12 | P0 |
| Configure OIDC deploy roles in AWS (no long-lived keys) | §12 | P0 |
| Set up `.pre-commit-config.yaml` (ruff, mypy, bandit, detect-secrets, hadolint) | §13 | P0 |
| Write `docker-compose.yml` for local dev (api + chromadb + dynamodb-local) | §16 | P0 |
| Write `Makefile` with dev shortcuts | §16 | P1 |
| Set up GitHub environments (staging, production) with approval gates | §12 | P1 |
| Configure AWS SES for email notifications (verify sender domain) | §15 | P1 |

**Skills required:** Terraform, AWS (ECS Fargate, IAM, VPC), Docker, GitHub Actions, Linux
**Dependencies on others:** Needs Person 3's API image to deploy. Can start immediately with infra.

---

## Person 2 — AI Agent + ML Pipeline
**Focus:** Agent orchestrator, tool calling, LLM service, embeddings, vector store, ingestion pipeline, knowledge base

| Task | Plan Reference | Priority |
|------|---------------|----------|
| Implement `agent/orchestrator.py` — main agent loop (receive → LLM → tool call → respond) | §3 | P0 |
| Implement `agent/tool_registry.py` — maps tool names → functions + JSON schemas for Groq | §3 | P0 |
| Write `agent/system_prompt.py` — versioned system prompt template | §3 | P0 |
| Implement `agent/tools/search_kb.py` — RAG search tool (calls VectorService) | §3, Tool 1 | P0 |
| Implement `agent/tools/fund_nav.py` — NAV lookup from DynamoDB | §3, Tool 2 | P0 |
| Implement `agent/tools/fund_perf.py` — performance metrics lookup | §3, Tool 3 | P0 |
| Implement `agent/tools/compare.py` — multi-fund comparison | §3, Tool 4 | P1 |
| Implement `agent/tools/risk_profile.py` — risk scoring algorithm + fund recommendation | §3, Tool 5 | P0 |
| Implement `agent/tools/escalate.py` — ticket creation + SES email trigger | §3, Tool 6 | P1 |
| Implement `services/llm_service.py` — Groq client with tool calling support | §3 | P0 |
| Implement `services/embedding_service.py` — sentence-transformers (local, 384d) | §4 | P0 |
| Implement `services/vector_service.py` — ChromaDB upsert, search, delete | §4 | P0 |
| Implement `services/document_processor.py` — PDF/DOCX/MD parsing + chunking (512 tokens) | §4 | P0 |
| Implement `pipeline/ingestion.py` — full pipeline: S3 → parse → chunk → embed → ChromaDB | §9 | P0 |
| Write `knowledge_base/scripts/seed.py` — download Al Meezan + MUFAP + SECP docs | §4 | P0 |
| Write fund data seeder — parse MUFAP NAV table → populate DynamoDB `funds` table | §4 | P0 |
| Write unit tests (tools, orchestrator, risk profile, chunking, embeddings) | §14 | P1 |

**Skills required:** LLM APIs (Groq/OpenAI tool calling), Python async, NLP (embeddings, chunking), ChromaDB, prompt engineering
**Dependencies:** Needs Person 3's `fund_data_service` and DynamoDB tables. Can start orchestrator + embedding service immediately with mocks.
**This is the hardest role** — requires understanding of tool calling, multi-turn conversations, RAG pipeline, and prompt design.

---

## Person 3 — Backend API / Services
**Focus:** FastAPI app, routers, DynamoDB operations, WebSocket, auth, email

| Task | Plan Reference | Priority |
|------|---------------|----------|
| Implement `main.py` — FastAPI app factory, CORS, lifespan, router mounts | §10 | P0 |
| Implement `core/config.py` — pydantic-settings for all env vars | §15 | P0 |
| Implement `core/dynamo.py` — DynamoDB client + table helpers | §5 | P0 |
| Implement `core/dynamo_init.py` — CLI script to create all 7 tables locally | §5 | P0 |
| Implement `core/security.py` — JWT sign/verify, bcrypt | §6 | P0 |
| Implement `core/dependencies.py` — `get_current_user`, `require_admin` | §6 | P0 |
| Implement `routers/chat_ws.py` — WebSocket endpoint (connect, receive, stream) | §6 | P0 |
| Implement `routers/conversations.py` — admin list/view conversations | §6 | P1 |
| Implement `routers/tickets.py` — ticket CRUD (create, assign, resolve) | §6 | P0 |
| Implement `routers/documents.py` — upload, list, delete, reindex | §6 | P1 |
| Implement `routers/funds.py` — fund data endpoints for tools | §6 | P1 |
| Implement `routers/ratings.py` — response quality ratings | §6 | P2 |
| Implement `routers/auth.py` — login, me | §6 | P0 |
| Implement `services/fund_data_service.py` — DynamoDB fund queries | §5 | P0 |
| Implement `services/storage_service.py` — S3 upload/download | §6 | P1 |
| Implement `services/email_service.py` — SES ticket confirmation + alerts | §2 | P1 |
| Write integration tests (WebSocket flow, ticket CRUD, auth) | §14 | P1 |

**Skills required:** FastAPI, Python async, DynamoDB (boto3), WebSocket, JWT
**Dependencies:** Can start immediately. Person 2 depends on this for tool data access.

---

## Person 4 — Chat Widget + Data Collection
**Focus:** Embeddable JS chat widget, WebSocket client, customer-facing UI

| Task | Plan Reference | Priority |
|------|---------------|----------|
| Build `widget/widget.js` — self-contained IIFE, WebSocket client, message rendering | §7 | P0 |
| Build `widget/widget.css` — chat bubble styles, responsive, Al Meezan branding (#006B3F) | §7 | P0 |
| Build `widget/widget.html` — local dev test page | §7 | P0 |
| Build `widget/demo.html` — mock Al Meezan landing page with widget embedded | §7 | P0 |
| Handle tool call indicators in widget ("🔍 Looking up fund data...") | §7 | P1 |
| Handle source citations display (collapsible after agent response) | §7 | P1 |
| Implement risk profiling UI flow (structured question prompts from agent) | §3, Tool 5 | P1 |
| Implement escalation flow in widget (collect customer email/phone) | §3, Tool 6 | P1 |
| Connection handling: auto-reconnect, offline state, typing indicator | §7 | P1 |
| Session persistence: `sessionStorage` for conversationId | §7 | P2 |

**Skills required:** HTML, CSS, JavaScript (vanilla), WebSocket API
**Dependencies:** Needs Person 3's WebSocket endpoint. Can start immediately with mock WebSocket server.
**Good for a less experienced developer** — mostly JS/CSS with clear specs.

---

## Person 5 — Admin Dashboard UI
**Focus:** Admin panel pages, Jinja2 templates, HTML/CSS, data tables

| Task | Plan Reference | Priority |
|------|---------------|----------|
| Build `admin/templates/base.html` — layout with navigation sidebar | §8 | P0 |
| Build `admin/templates/login.html` — email + password form | §8 | P0 |
| Build `admin/templates/dashboard.html` — overview stats (active convos, open tickets, quality %) | §8 | P0 |
| Build `admin/templates/conversations.html` — list with filters (status, date range) | §8 | P0 |
| Build `admin/templates/conversation_detail.html` — full transcript with tool calls highlighted | §8 | P0 |
| Build `admin/templates/tickets.html` — ticket queue with status/priority filters, assign/resolve | §8 | P0 |
| Build `admin/templates/knowledge_base.html` — doc list, upload form, delete, reindex buttons | §8 | P1 |
| Build `admin/templates/quality.html` — rating stats + Chart.js trends | §8 | P2 |
| Build `admin/templates/funds.html` — fund data table, trigger refresh | §8 | P2 |
| Build `admin/views.py` — FastAPI route handlers that render templates | §8 | P0 |
| Build `admin/static/` — admin CSS + JS (DataTables, forms, modals) | §8 | P0 |

**Skills required:** HTML, CSS, JavaScript, Jinja2, basic Python (FastAPI route handlers)
**Dependencies:** Needs Person 3's REST API endpoints. Can start layout + static HTML immediately.
**Good for a less experienced developer** — mostly HTML/CSS with clear API contracts in the plan.

---

## Dependency Graph

```
                Person 1 (Infra)
               ┌─────────────────┐
               │ Terraform, ECS, │
               │ CI/CD, Docker   │
               └────────┬────────┘
                        │ deploys all services
                        ▼
Person 4 (Widget) ◄──── Person 3 (Backend API) ◄──── Person 2 (AI + ML)
┌──────────────────┐    ┌───────────────────┐       ┌──────────────────┐
│ Chat Widget      │    │ FastAPI, WebSocket │       │ Agent, Tools,    │
│ JS/CSS           │    │ DynamoDB, Auth     │       │ Embeddings,      │
└──────────────────┘    └────────┬──────────┘       │ ChromaDB, KB     │
                                 │ provides API      └──────────────────┘
                       Person 5 (Admin UI)
                       ┌──────────────────┐
                       │ Admin Dashboard  │
                       │ Jinja2, HTML/CSS │
                       └──────────────────┘
```

---

## 1-Week Sprint Plan (7 Days)

### Day 1–2: Foundation (all parallel, no cross-dependencies)

| Person | Deliverable | Done when |
|--------|------------|-----------|
| P1 | Docker Compose local dev, Dockerfiles, pre-commit hooks, CI workflow | `make dev` starts all services |
| P2 | Agent orchestrator + 2 tools (search_kb, fund_nav) with mocks, embedding service working | Agent responds to test prompts |
| P3 | FastAPI app, auth (login/JWT), DynamoDB tables, WebSocket endpoint (echo mode) | `/docs` shows all routes, WS echoes |
| P4 | Chat widget connects to WS, sends/receives messages, basic styling | Widget opens and sends messages |
| P5 | Admin login page + base layout with navigation sidebar | Admin panel skeleton loads |

### Day 3–4: Integration (wire everything together)

| Person | Deliverable | Done when |
|--------|------------|-----------|
| P1 | Terraform staging (`vpc`, `ecs`, `dynamodb`, `s3`, `iam`), staging deploy workflow | `terraform plan` succeeds |
| P2 | All 6 tools wired, ingestion pipeline end-to-end, fund data seeded, risk profiling flow | Full chat conversation works end-to-end |
| P3 | All routers complete (tickets, documents, funds, ratings), SES email service | Admin API endpoints all functional |
| P4 | Tool call indicators, source citations, escalation form (collect email/phone) | Widget handles all message types |
| P5 | Conversations list + detail, ticket queue with filters, KB management page | Admin panel fully navigable |

### Day 5–6: Polish + Test

| Person | Deliverable | Done when |
|--------|------------|-----------|
| P1 | Prod Terraform, prod deploy workflow, deploy to staging | Staging is live |
| P2 | Prompt tuning, edge case handling, test 20 real queries, seed script finalized | 80%+ queries answered correctly |
| P3 | Error handling, integration tests, rate limiting | All tests green |
| P4 | Responsive polish, auto-reconnect, demo.html landing page | Widget looks production-ready |
| P5 | Dashboard stats, quality page (Chart.js), responsive polish | Admin panel looks professional |

### Day 7: Deploy + Demo

| Person | Task |
|--------|------|
| P1 | Deploy to production, verify health checks |
| P2 | Demo script: 10 conversations covering all 6 tools |
| P3 | Seed prod DynamoDB tables, load test |
| P4 | Final widget review, cross-browser check |
| P5 | Final admin review, cross-browser check |

> **Scope cut for 1-week deadline:** Quality dashboard charts are a nice-to-have. Core deliverable = working chat widget + admin panel + all 6 tools + deployed on AWS.

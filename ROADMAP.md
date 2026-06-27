# Public Roadmap — AI Contact Center Starter Kit

This is a living document. Items move between milestones as priorities shift.
Contributions that advance any milestone are welcome — see
[`CONTRIBUTING.md`](CONTRIBUTING.md).

> **Last updated:** June 2026

---

## ✅ v0.1.0 — Foundation (Released)

- [x] FastAPI backend with WebSocket chat
- [x] OpenAI tool calling orchestration loop
- [x] RAG pipeline: PDF ingestion → ChromaDB → semantic search
- [x] Live data tools (scraping pattern with fallback to static cache)
- [x] Fine-tuning pipeline: S3 → Lambda → OpenAI FT Jobs
- [x] DynamoDB data model (conversations, messages, ratings, prompts)
- [x] Langfuse LLM observability (auto-tracing)
- [x] Vanilla JS embeddable chat widget
- [x] Jinja2 admin dashboard (conversations, LLMOps, ratings)
- [x] Terraform modular infrastructure (VPC, ECS Fargate, ECR, IAM, S3, Lambda, CodeDeploy)
- [x] GitHub Actions CI/CD with OIDC (no static AWS keys)
- [x] Pre-commit SAST: bandit, semgrep, detect-secrets, ruff, mypy
- [x] Blue/Green deployment via AWS CodeDeploy
- [x] SES email escalation to human agents
- [x] MIT License
- [x] CONTRIBUTING.md, SECURITY.md, ROADMAP.md

---

## 🚧 v0.2.0 — Streaming & Multi-Tenancy *(In Progress)*

- [ ] **Streaming responses** — Server-Sent Events (SSE) for token-by-token streaming
- [ ] **Multi-tenant support** — tenant_id isolation in DynamoDB + ChromaDB namespaces
- [ ] **OpenAI Assistants API adapter** — drop-in swap for Assistants API vs. manual tool calling
- [ ] **Rate limiting** — per-tenant API rate limiting middleware
- [ ] **Conversation history management** — token-aware history truncation
- [ ] **Eval framework** — automated golden dataset evals with Langfuse scores
- [ ] **Docker Compose production profile** — Traefik reverse proxy + SSL termination

---

## 📋 v0.3.0 — Adapters & Integrations

- [ ] **Ticketing system adapter** — pluggable interface for Zendesk / Jira / Linear
- [ ] **CRM connector** — Salesforce / HubSpot contact lookup tool
- [ ] **Authentication providers** — OAuth2 / SAML for admin panel
- [ ] **Webhook outbound events** — notify external systems on escalation / conversation end
- [ ] **Vector store adapters** — Pinecone, Weaviate, pgvector as ChromaDB alternatives
- [ ] **LLM provider adapters** — Anthropic Claude, Gemini, Mistral as OpenAI alternatives

---

## 🔭 v0.4.0 — Developer Experience

- [ ] **`create-ai-contact-center` CLI** — `npx create-ai-contact-center my-app` scaffolding
- [ ] **One-click deploy to AWS** — CloudFormation template or CDK wrapper
- [ ] **Local dev with DynamoDB + ChromaDB** — single `docker compose up` with no AWS account needed
- [ ] **Interactive tutorial** — step-by-step guide to building your first custom tool
- [ ] **Demo video and screenshots** — hosted demo environment

---

## 💡 Backlog (No Milestone Yet)

- Mobile-friendly admin dashboard
- Voice / telephony adapter (Twilio)
- Real-time agent monitoring dashboard
- A/B prompt testing UI (architecture already supports it)
- Kubernetes Helm chart alternative to ECS
- LangSmith as alternative to Langfuse

---

## How to Influence the Roadmap

- **Vote on issues** — 👍 reactions on issues signal priority
- **Open a feature request** — use the Feature Request issue template
- **Submit a PR** — working code moves things faster than discussion

---

*Maintainer note: this roadmap reflects current intent, not a commitment. Timelines may shift.*

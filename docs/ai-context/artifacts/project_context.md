# Alfalah AI Contact Centre — Project Knowledge Item

## Project Location
`/home/saad/Documents/Code/Devops/Project/`

## What This Is
A production-grade AI customer support chatbot for **Alfalah Investments** (Alfalah AMC), a mutual fund asset management company in Pakistan. The chatbot is named "Alfalah GPT" and handles customer queries about mutual fund NAVs, fund performance, account opening, and escalation to human agents.

---

## Tech Stack
| Layer | Technology |
|-------|-----------|
| LLM | OpenAI GPT-4o-mini (fine-tuned) |
| Agent Framework | OpenAI Tool Calling (native, no LangChain) |
| Observability | Langfuse (auto-tracing via `langfuse.openai.AsyncOpenAI`) |
| RAG | ChromaDB + `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |
| Backend API | FastAPI + WebSockets |
| Database | AWS DynamoDB (conversations, messages, prompts, models, ratings) |
| Storage | AWS S3 (raw training data, cleaned JSONL) |
| Data Processing | AWS Lambda (S3 trigger → clean → JSONL) |
| Infrastructure | Terraform (modular: vpc, ecs, ecr, iam, s3, lambda, sns, code_deploy) |
| Deployment | AWS ECS Fargate + CodeDeploy Blue/Green |
| CI/CD | GitHub Actions with OIDC (no static AWS keys) |
| Secrets | AWS Secrets Manager |
| Notifications | AWS SES (escalation emails) |
| Frontend | Vanilla JS chat widget + Jinja2 admin dashboard |

---

## Repository Structure
```
Project/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── orchestrator.py          # Main LLM loop with tool handling
│   │   │   ├── tool_registry.py         # Tool schemas + dispatcher
│   │   │   └── tools/
│   │   │       ├── get_fund_nav.py      # Live scraper: NAV
│   │   │       ├── get_fund_performance.py  # Live scraper: returns
│   │   │       └── search_kb.py         # RAG search tool
│   │   ├── services/
│   │   │   ├── embedding_service.py     # sentence-transformers
│   │   │   ├── vector_service.py        # ChromaDB CRUD
│   │   │   ├── finetuning_service.py    # S3 → OpenAI FT job
│   │   │   └── email_service.py         # SES escalation emails (TODO)
│   │   ├── pipeline/
│   │   │   └── ingestion.py             # PDF → chunks → ChromaDB
│   │   └── routers/ (TODO - Person 3)
│   ├── scripts/lambda_processor/main.py # S3 trigger → JSONL
│   └── Dockerfile                       # Multi-stage, Python 3.11-slim
├── infrastructure/
│   ├── terraform/
│   │   ├── modules/                     # vpc, ecs, ecr, iam, s3, lambda, sns, code_deploy
│   │   └── environments/staging/, prod/ # .tfvars populated
│   └── codedeploy/appspec.yaml + taskdef.json
├── .github/workflows/deploy.yml         # OIDC → ECR → CodeDeploy
├── .pre-commit-config.yaml              # ruff, black, mypy, bandit, semgrep, detect-secrets
├── knowledge_base/
│   ├── scripts/seed.py                  # Downloads real Alfalah PDFs + scrapes FAQs
│   └── scripts/prepare_ft_data.py       # Converts FAQs → OpenAI JSONL locally
└── docs/
    ├── ARCHITECTURE_DECISIONS.md        # WHY decisions were made (ADRs)
    ├── DATA_GATHERING_GUIDE.md          # What data to get, how to process it
    ├── INFRASTRUCTURE_CHECKLIST.md      # What's done / what's remaining
    └── WIDGET_DATA_COLLECTION.md        # Widget data spec (deleted - replaced by ADR)
```

---

## Key Architectural Decisions (summary — see ADRs for full rationale)
1. **OpenAI not Groq** — fine-tuning API requirement
2. **Live scraping not internal APIs** — Alfalah doesn't expose APIs
3. **3 data pipelines** — scraping (NAV), RAG (PDFs), fine-tuning (FAQs/tone)
4. **HTTP only, no domain** — demo uses ALB DNS + `demo.html` mock page
5. **CodeDeploy Blue/Green** — zero downtime for financial services
6. **OIDC not static keys** — security best practice
7. **Secrets Manager** — keys never in plaintext env vars
8. **Escalation via SES email** — no Jira/Zendesk, just DynamoDB log + email

---

## Data Sources (Real, Live)
- **RAG PDFs:** `https://alfalahamc.com/downloads/offering-documents/` — Offering Documents, Trust Deeds
- **Fine-Tuning Text:** `https://alfalahamc.com/faqs/`, `/taxation/`, `/terms-conditions/`
- **Live NAV:** `https://alfalahamc.com/fund-prices` + `https://mufap.com.pk`
- **Seed script:** `knowledge_base/scripts/seed.py` downloads all of the above

---

## People / Team
- **Person 1 (DevOps):** Terraform, CI/CD, Docker, pre-commit — **COMPLETE**
- **Person 2 (AI/ML):** Agent, tools, RAG, embeddings, fine-tuning — **COMPLETE**
- **Person 3 (Backend):** FastAPI, WebSockets, DynamoDB, Lambda — **IN PROGRESS**
- **Person 4 (Widget):** JS chat widget, demo.html — **TODO**
- **Person 5 (Admin UI):** Jinja2 dashboard, LLMOps UI — **TODO**

---

## Scope Exclusions
- No HTTPS / custom domain (HTTP ALB DNS only)
- No Jira/Zendesk ticketing (SES email escalation)
- No mobile app (web widget only)
- No A/B prompt testing UI in v1 (architecture supports it)
- MeezanGPT is primarily an internal tool — our scope is more advanced (public-facing widget)

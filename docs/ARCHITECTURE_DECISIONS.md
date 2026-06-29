# Architecture Decision Records (ADR)
## Alfalah Investments AI Contact Centre

This document captures the key design decisions, scope changes, and rationale from the project's initial planning sessions. It is intended to give new team members full context on *why* the system is built the way it is.

---

## ADR-001: Pivot from Groq/Llama to OpenAI GPT-4o-mini
- **Decision:** Use OpenAI `gpt-4o-mini` as the primary LLM instead of Groq (Llama 3.1 70B).
- **Rationale:** OpenAI is the only provider offering a self-service, programmable fine-tuning API (`fine_tuning.jobs.create`). Since a core requirement is an automated fine-tuning pipeline triggered by new training data uploads, OpenAI was the only viable option. Groq does not support fine-tuning.
- **Trade-off:** OpenAI is slightly more expensive per token than Groq, but `gpt-4o-mini` is cost-efficient and the fine-tuning capability justifies it.

---

## ADR-002: Live Web Scraping Instead of Internal APIs for NAV/Performance
- **Decision:** Use `httpx` + `BeautifulSoup4` to scrape NAV and performance data from `alfalahamc.com` at runtime rather than integrating with internal Alfalah APIs.
- **Rationale:** Alfalah Investments does not provide internal REST APIs accessible to us. Public mutual fund data (NAVs, returns) is publicly available on their website and on `mufap.com.pk`.
- **Risk:** This approach is fragile — if Alfalah changes their website HTML structure, the scraper breaks. The `get_fund_nav.py` and `get_fund_performance.py` tools will need to be updated when that happens.
- **Mitigation:** Scraping logic is isolated in individual tool files so it can be fixed independently.

---

## ADR-003: Data Split — RAG vs Fine-Tuning vs Scraping
- **Decision:** Use three separate pipelines for different types of data.
- **Rationale:**
  | Data Type | Pipeline | Reason |
  |-----------|----------|--------|
  | NAVs, performance | Live Scraping | Changes daily — cannot be stored |
  | Prospectuses, FMRs, SECP regulations | RAG (ChromaDB) | Too large for fine-tuning; exact retrieval needed |
  | FAQs, tone, agent behavior | Fine-Tuning | Teaches the model *how* to respond |
- **Key insight:** Fine-tuning is NOT used for memorizing facts. It teaches tone, disclaimer injection, and when to call which tool.

---

## ADR-004: No Domain / No SSL (HTTP-Only Deployment)
- **Decision:** Deploy on AWS ECS Fargate behind an Application Load Balancer using HTTP only. No custom domain, no ACM TLS certificates.
- **Rationale:** The project does not currently have access to the Alfalah website domain. The ALB's raw DNS name (`alfalah-ai-prod-alb-xxxxxxx.us-east-1.elb.amazonaws.com`) is used as the endpoint.
- **Demo Strategy:** A `demo.html` file is served by FastAPI that simulates the Alfalah website for stakeholder demos, making the domain unnecessary during development and the initial demo phase.
- **Future:** When Alfalah provides domain access, add ACM certificate + HTTPS listener to the `load_balancer` Terraform module.

---

## ADR-005: AWS CodeDeploy Blue/Green Deployment
- **Decision:** Use AWS CodeDeploy with a Blue/Green deployment strategy for ECS updates instead of standard rolling updates.
- **Rationale:** In a financial services context, downtime during deployments is unacceptable. Blue/Green keeps the old ("blue") task set running while the new ("green") one starts and health checks pass. Traffic is only switched after successful health verification, with automatic rollback on failure.
- **Implementation:** Two ALB Target Groups (`tg-blue`, `tg-green`) + a `code_deploy` Terraform module + `appspec.yaml` + `taskdef.json`.

---

## ADR-006: GitHub Actions OIDC Instead of Static AWS Access Keys
- **Decision:** Configure GitHub Actions to use OpenID Connect (OIDC) `role-to-assume` instead of storing `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as GitHub Secrets.
- **Rationale:** Static long-lived access keys are a critical security risk, especially in a financial services project. OIDC generates short-lived (~1 hour) temporary credentials per GitHub Actions run. If a secret is ever leaked, there is no key to steal.
- **Implementation:** `infrastructure/terraform/modules/iam/oidc.tf` provisions the OIDC Identity Provider in AWS and the `github-actions-deploy-role` IAM role with trust restricted to the `main` branch only.

---

## ADR-007: AWS Secrets Manager for API Keys
- **Decision:** Store sensitive API keys (`OPENAI_API_KEY`, `LANGFUSE_SECRET_KEY`, `JWT_SECRET_KEY`) in AWS Secrets Manager, not as plain-text ECS environment variables.
- **Rationale:** Plain-text environment variables in ECS Task Definitions are visible to anyone with IAM read access to the task definition. Secrets Manager encrypts them at rest and provides access logging.
- **Implementation:** The ECS Task Execution Role has `secretsmanager:GetSecretValue` policy attached (see `iam/main.tf`). ECS resolves secrets at container startup via the `secrets` block in the task definition.

---

## ADR-008: Langfuse for LLMOps Observability (Free Tier)
- **Decision:** Use Langfuse (cloud, free tier) for LLM tracing, evaluation, and observability.
- **Rationale:** Langfuse provides detailed traces of every LLM call (model, tokens, latency, inputs/outputs) and integrates natively with the OpenAI Python SDK via `langfuse.openai.AsyncOpenAI`. It is free for our scale.
- **Alternative considered:** MLflow — rejected as it requires self-hosting and has no native OpenAI trace wrapping.

---

## ADR-009: Escalation via Email (No Ticketing System)
- **Decision:** When a user asks to speak to a human, the AI collects their name, email, and query description conversationally, then sends an email to the Alfalah support team via AWS SES. The escalation is logged to DynamoDB.
- **Rationale:** Meezan Bank (our benchmark) does not use an AI-triggered ticketing system. They use a simple email/complaint form flow. Integrating with a full ticketing platform (Jira, Zendesk) is significant scope and unnecessary for the demo.
- **Implementation:** `escalate_to_human` tool in `tool_registry.py` → `services/email_service.py` using `boto3` SES → admin can view all escalations in the admin panel.

---

## ADR-010: Pre-commit Hooks Including SAST
- **Decision:** Enforce code quality at commit time using `.pre-commit-config.yaml` with `ruff` (linting), `black` (formatting), `mypy` (type checking), `bandit` (security), `semgrep` (SAST), and `detect-secrets` (credential scanning).
- **Rationale:** This is a financial services project. Any accidentally committed secret or security vulnerability should be caught before it ever reaches the remote repository.

---

## Scope Notes

### What MeezanGPT Does (our benchmark)
- MeezanGPT is a Generative AI initiative by Meezan Bank in collaboration with Ekkel AI, primarily for **internal employee productivity** — not a public-facing customer chatbot with ticket creation.
- Their public customer support escalation is via static channels: email `complaints@meezanbank.com`, complaint forms on the website, and call centres.
- **Conclusion:** Our scope of an AI chat widget on the public-facing website is actually *more advanced* than MeezanGPT's current implementation.

### What's Out of Scope (Deliberately)
- **No HTTPS/Custom Domain** — uses ALB raw DNS for now.
- **No Jira/Zendesk integration** — email escalation is sufficient.
- **No A/B prompt testing** — prompt registry supports it architecturally but no UI for it in v1.
- **No mobile app** — widget is web-only.

---

## ADR-011: Pluggable Vector Store with Optional pgvector Backend
- **Decision:** Introduce a small `VectorStore` Protocol abstraction and ship two adapters: `ChromaVectorStore` (default, preserves existing behavior) and `PgVectorStore` (PostgreSQL + pgvector, opt-in via `VECTOR_STORE_TYPE=pgvector`).
- **Rationale:** ChromaDB is ideal for local development and single-node deployments, but production environments often require a managed, durable, shared PostgreSQL instance. pgvector is the lowest-friction Postgres-native vector option and pairs naturally with AWS RDS / Cloud SQL.
- **Key constraints:**
  - ChromaDB remains the default; no existing user needs to change config.
  - The public async API in `vector_service.py` is preserved exactly — zero caller changes.
  - pgvector stores **pre-generated embeddings** from the existing `embedding_service`; no embedding generation moves into Postgres.
  - Uses `psycopg3` + `psycopg_pool` (no SQLAlchemy — the project uses raw `boto3` for DynamoDB and prefers explicit drivers).
  - Metadata is stored as JSONB with a GIN index; `source` is a top-level column for efficient source-based deletes.
  - Cosine distance (`<=>`) matches ChromaDB's `hnsw:space: cosine` semantics so distance values are comparable across backends.
- **Trade-off:** The `/api/v1/chroma` admin endpoints are ChromaDB-specific; they return `NotImplementedError` when pgvector is selected. Acceptable for v1.
- **Future:** Additional backends (Qdrant, Weaviate, Pinecone) can be added by implementing the `VectorStore` Protocol and registering in the factory.

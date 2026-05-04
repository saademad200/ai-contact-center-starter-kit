# Project Plan: Alfalah Investments AI Contact Centre

> A production-ready, cost-optimized AI customer service system designed to mimic the scope of "Meezan GPT" for **Alfalah Investments**. It uses **OpenAI (gpt-4o-mini)**, extensive tool calling, and automated fine-tuning pipelines.

## 1. System Architecture

### Core Tech Stack
- **LLM Provider:** OpenAI (`gpt-4o-mini` base, with custom fine-tuned variants).
- **Observability:** Langfuse (Trace logging, Eval metrics).
- **Agent Orchestrator:** Python + FastAPI.
- **Backend/Admin:** FastAPI + Jinja2 (server-side rendering).
- **Frontend Widget:** Vanilla JS + CSS (WebSocket).
- **Vector DB:** ChromaDB (for RAG).
- **State/Registry DB:** AWS DynamoDB (Conversations, Prompt Registry, Model Registry).
- **Secrets:** AWS Secrets Manager (for OpenAI/Langfuse keys).
- **Data Pipeline:** AWS S3 + AWS Lambda (Data cleaning & JSONL conversion).
- **Hosting:** AWS ECS Fargate + ALB + CodeDeploy (Blue/Green).

### Component Diagram

```
[Customer Website] ──(WebSocket)──▶ [ALB] ──▶ [FastAPI App (Fargate)]
                                                  │
                                                  ├─▶ [OpenAI API] (Fine-Tuned Model)
                                                  │      └─▶ [Langfuse] (Observability)
                                                  │
                                                  ├─▶ [Agent Tools]
                                                  │      ├─▶ [Live Web Scraping] (MUFAP/Alfalah)
                                                  │      └─▶ [ChromaDB] (RAG)
                                                  │
     ┌────────────────────┐     ┌────────────────┐│
     │  Admin Panel       │     │ DynamoDB       ││
     │  (FastAPI + HTML)  │────▶│ (Registries &  │◀
     │  KB + LLMOps UI    │     │  Conversations)│
     └────────────────────┘     └────────────────┘
              │
         (Uploads Docs)
              ▼
          [AWS S3]
              │
        (S3 Event)
              ▼
        [AWS Lambda] ──(Cleans & formats to JSONL)──▶ [S3 Cleaned] ──(Admin Trigger)──▶ [OpenAI Fine-Tuning]
```

---

## 2. LLMOps & Data Strategy

We split data handling into three distinct paths to optimize LLM performance and reduce costs.

1. **Fine-Tuning (Tone & General Knowledge):**
   - *Data:* FAQs, customer service transcripts, standard policies, conversational tone.
   - *Pipeline:* Admin uploads text/docx to S3 `raw/` -> Lambda strips T&Cs/formats -> saves to S3 `cleaned.jsonl` -> Admin manually triggers OpenAI fine-tuning job.
2. **RAG (Complex/Long Documents):**
   - *Data:* Detailed prospectuses, Fund Manager Reports (FMRs), SECP regulations.
   - *Pipeline:* Admin uploads PDF -> API chunks & embeds (sentence-transformers) -> ChromaDB.
3. **Live Web Scraping (Real-time Volatile Facts):**
   - *Data:* Daily NAVs, Fund performance metrics.
   - *Pipeline:* Agent tools use `BeautifulSoup4` and `httpx` to dynamically scrape MUFAP (Mutual Funds Association of Pakistan) or the Alfalah AMC website on-the-fly during a customer conversation.

### Registries (DynamoDB)
Instead of hardcoding prompts and models, the app fetches the active state from DynamoDB on startup/cache-refresh:
- **Prompt Registry:** Stores `system_prompt` texts. Allows rollback and A/B testing.
- **Model Registry:** Tracks OpenAI fine-tuning job IDs and the resulting `ft:gpt-4o-mini-...` model IDs.

---

## 3. Agent Tools

The agent uses OpenAI Tool Calling to invoke functions based on customer intent.

1. **`search_knowledge_base`**: Performs semantic search against ChromaDB for complex procedural questions (e.g., "What are the tax implications in the prospectus?").
2. **`get_fund_nav`**: Scrapes MUFAP.com.pk or AlfalahAMC.com on-the-fly to extract the live daily NAV for a specific fund.
3. **`get_fund_performance`**: Scrapes public fund profiles dynamically to extract YTD, 1Y, 3Y returns.
4. **`compare_funds`**: Aggregates scraped data from two funds to compare them side-by-side.
5. **`escalate_to_human` (Optional)**: If the user needs account-specific help, collects their email and logs a ticket in DynamoDB (triggering an SES email to the support team).

---

## 4. Database Schema (DynamoDB)

### 1. `alfalah-prompt-registry`
- `version_id` (PK) - e.g., `v1.0.3`
- `prompt_text` (String)
- `created_at` (ISO timestamp)
- `active_status` (Boolean)

### 2. `alfalah-model-registry`
- `job_id` (PK) - OpenAI ftjob id
- `openai_model_id` (String) - e.g., `ft:gpt-4o-mini-2024-07-18:org:custom:id`
- `status` (String) - running, succeeded, failed
- `base_model` (String)
- `active_status` (Boolean)

### 3. `conversations`
- `conversation_id` (PK)
- `user_id` (String)
- `created_at` (ISO timestamp)
- `status` (active, resolved, escalated)

### 4. `messages`
- `conversation_id` (PK)
- `timestamp_id` (SK) - UUID sort key for chronological ordering
- `role` (user, assistant, tool)
- `content` (String)
- `tool_calls` (JSON string - optional)

### 5. `response-ratings`
- `rating_id` (PK)
- `conversation_id` (String)
- `rating` (good, bad, incorrect)
- `feedback` (String)

---

## 5. Admin Dashboard UI

A Jinja2-rendered server-side UI protected by JWT authentication.

- **/admin/dashboard:** Overview stats (Active conversations, Accuracy rate from ratings).
- **/admin/llmops:**
  - View Prompt Registry (Create new version, set active).
  - View Model Registry (Check FT status, set active model).
  - "Trigger Fine-Tuning" button (takes the latest `cleaned.jsonl` from S3 and starts an OpenAI job).
- **/admin/knowledge_base:** Upload documents. Toggle switch to route document to "RAG Database" or "Fine-tuning Training Data".
- **/admin/conversations:** View transcripts.
- **/admin/tickets:** Support queue.

---

## 6. Development & Deployment

### CI/CD (GitHub Actions)
1. **`ci.yml`**: Runs `pytest`, `ruff`, `mypy`. Also runs `scripts/evaluate_agent.py` against `tests/eval/golden_dataset.json` to ensure prompt/tool accuracy > 90%.
2. **`deploy.yml`**: Builds Docker image, pushes to ECR, and triggers **AWS CodeDeploy (Blue/Green)** to update the ECS Fargate service without downtime.
3. **`terraform.yml`**: Plans and applies infra changes.

### Environment Variables & Secrets
```bash
# App Configuration (injected via ECS task definition env vars)
ENVIRONMENT=development
AWS_REGION=us-east-1
S3_BUCKET_NAME=alfalah-data-prod
DYNAMODB_ENDPOINT_URL= # blank for AWS, set for local dev

# Sensitive API Keys (Pulled dynamically via AWS Secrets Manager)
# - OPENAI_API_KEY
# - LANGFUSE_PUBLIC_KEY
# - LANGFUSE_SECRET_KEY
# - JWT_SECRET_KEY
```

# Internal Banking Knowledge Management System (KMS)
## Complete Project Plan — Team Reference Document

**Version:** 1.0 | **Status:** Approved for Development | **Date:** April 2026
**Audience:** All engineering team members, QA, DevOps

> This document is the **single source of truth** for building the KMS platform.
> A developer reading only this document should be able to build their assigned module correctly.

---

## Table of Contents

1. [Problem Statement & Goals](#1-problem-statement--goals)
2. [System Architecture](#2-system-architecture)
3. [Repository Structure](#3-repository-structure)
4. [Branch & Environment Strategy](#4-branch--environment-strategy)
5. [Knowledge Base Design (Two-Layer)](#5-knowledge-base-design-two-layer)
6. [Data Models (DynamoDB Schemas)](#6-data-models-dynamodb-schemas)
7. [API Contract (All Endpoints)](#7-api-contract-all-endpoints)
8. [Core Service Interfaces](#8-core-service-interfaces)
9. [Key System Flows (Sequence Diagrams)](#9-key-system-flows-sequence-diagrams)
10. [Infrastructure (Terraform)](#10-infrastructure-terraform)
11. [CI/CD Pipelines (GitHub Actions)](#11-cicd-pipelines-github-actions)
12. [Code Quality & Pre-commit Hooks](#12-code-quality--pre-commit-hooks)
13. [Testing Strategy](#13-testing-strategy)
14. [Environment Variables Reference](#14-environment-variables-reference)
15. [Local Development Setup](#15-local-development-setup)
16. [Frontend Pages & Components](#16-frontend-pages--components)
17. [Deployment Guide](#17-deployment-guide)

---

## 1. Problem Statement & Goals

### Problem
A software company building niche banking applications for Pakistani banks needs employees to quickly answer two types of questions:

**Type A — Domain questions:**
> "What is the SBP provisioning requirement for a Substandard loan?"
> "What documents are required for SME financing under SBP regulations?"

**Type B — Application questions:**
> "How does the loan rescheduling workflow work in our system?"
> "What API does the payment module call for IBFT transactions?"

Currently employees search Confluence, PDFs, and ask seniors — slow and inconsistent.

### Solution
An internal RAG-based chat system where employees describe their question in plain English and receive an accurate, sourced answer drawn from:
- SBP regulatory documents (Layer 1)
- HBL public annual reports as banking domain reference (Layer 2)
- Internal application documentation uploaded by admins (Layer 3)

### Non-Goals (out of scope for v1)
- Real-time data (stock prices, live rates)
- Code generation
- Multi-language support (English only)
- Customer-facing deployment

### Success Criteria
- Employee asks question → receives answer with source citation in < 10 seconds
- Answer correctly cites relevant SBP regulation or internal SOP
- Admin uploads a PDF → searchable within 5 minutes

---

## 2. System Architecture

### High-Level Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                    Employees (Browser)                         │
│                  Next.js 14 Chat Interface                     │
└───────────────────────────┬───────────────────────────────────┘
                            │ HTTPS (port 443)
                ┌───────────▼───────────┐
                │  ALB (AWS Application  │
                │   Load Balancer)       │
                └───────────┬───────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
┌───────▼────────┐                    ┌─────────▼──────────┐
│  API Service   │                    │  Frontend Service  │
│  FastAPI :8000 │                    │  Next.js :3000     │
│  ECS Fargate   │                    │  ECS Fargate       │
└───────┬────────┘                    └────────────────────┘
        │
        ├──────────────────────────────────────────────────┐
        │                                                  │
        ▼                                                  ▼
┌───────────────┐    ┌──────────────┐    ┌────────────────────┐
│  AWS DynamoDB │    │   AWS S3     │    │    ChromaDB        │
│  (metadata)   │    │ (raw docs)   │    │  (vector store)    │
│               │    │              │    │  ECS + EFS volume  │
└───────────────┘    └──────────────┘    └─────────┬──────────┘
                                                    │ similarity search
                                              ┌─────▼──────┐
                                              │ Groq API   │
                                              │ (or HF API)│
                                              │ Llama 3.1  │
                                              └────────────┘
```

### Component Responsibilities

| Component | Technology | Responsibility |
|-----------|-----------|----------------|
| **API Service** | FastAPI (Python 3.11), ECS Fargate | All business logic, RAG, auth |
| **Frontend** | Next.js 14, ECS Fargate | Chat UI, admin panel, auth pages |
| **DynamoDB** | AWS DynamoDB (PAY_PER_REQUEST) | Users, sessions, documents metadata, messages |
| **S3** | AWS S3 | Raw uploaded files (PDFs, DOCX, MD) |
| **ChromaDB** | ChromaDB container, EFS volume | Text chunk embeddings + similarity search |
| **Embeddings** | sentence-transformers MiniLM (local) | Convert text to 384-dim vectors, free |
| **LLM** | Groq API (Llama 3.1 70B, default) | Answer generation from retrieved context |
| **ALB** | AWS Application Load Balancer | HTTPS termination, routing |

---

## 3. Repository Structure

```
Project/                              ← monorepo root
│
├── .github/
│   ├── pull_request_template.md      ← PR checklist
│   └── workflows/
│       ├── ci.yml                    ← runs on ALL branches (lint + unit tests)
│       ├── staging.yml               ← push to staging → deploy ECS staging
│       ├── prod.yml                  ← push to main → deploy ECS prod (approval)
│       └── terraform.yml             ← push to infrastructure → tf plan/apply
│
├── infrastructure/
│   ├── docker/
│   │   ├── Dockerfile.api            ← multi-stage, Python 3.11-slim
│   │   └── Dockerfile.frontend       ← multi-stage, Node 20-alpine
│   └── terraform/
│       ├── backend.tf                ← S3 remote state + DynamoDB lock
│       └── modules/
│       │   ├── vpc/                  ← VPC, subnets, IGW, NAT, security groups
│       │   ├── ecs/                  ← Fargate cluster, task defs, ALB, services
│       │   ├── dynamodb/             ← All 4 tables with GSIs
│       │   ├── s3/                   ← Document bucket + lifecycle rules
│       │   └── iam/                  ← Task roles, GitHub OIDC role
│       └── environments/
│           ├── staging/              ← Fargate 0.25vCPU/0.5GB, 1 task
│           └── prod/                 ← Fargate 0.5vCPU/1GB, 2 tasks, PITR on
│
├── backend/                          ← FastAPI application (Python 3.11)
│   ├── app/
│   │   ├── main.py                   ← App factory, routers, CORS, lifespan events
│   │   ├── core/
│   │   │   ├── config.py             ← All settings via pydantic-settings
│   │   │   ├── dynamo.py             ← Boto3 DynamoDB client + table helpers
│   │   │   ├── dynamo_init.py        ← CLI script: create tables in DynamoDB Local
│   │   │   ├── security.py           ← JWT sign/verify, bcrypt hash/verify
│   │   │   ├── logging.py            ← structlog JSON logger
│   │   │   └── dependencies.py       ← FastAPI deps: get_current_user, require_admin
│   │   │
│   │   ├── modules/                  ← Feature modules (router + service + schemas)
│   │   │   ├── auth/
│   │   │   │   ├── router.py         ← POST /auth/login, /auth/refresh, GET /auth/me
│   │   │   │   ├── service.py        ← AuthService: login, create_user, verify_token
│   │   │   │   └── schemas.py        ← LoginRequest, TokenResponse, UserResponse
│   │   │   ├── documents/
│   │   │   │   ├── router.py         ← POST /documents/upload, GET /documents, DELETE /documents/{id}
│   │   │   │   ├── service.py        ← DocumentService: upload to S3, track in DynamoDB
│   │   │   │   └── schemas.py        ← DocumentUploadResponse, DocumentStatus, DocumentItem
│   │   │   ├── chat/
│   │   │   │   ├── router.py         ← POST /chat/sessions, POST /chat/message (SSE), GET /chat/sessions
│   │   │   │   ├── service.py        ← ChatService: create session, save message, get history
│   │   │   │   └── schemas.py        ← ChatMessage, ChatSession, ChatRequest, Source
│   │   │   └── admin/
│   │   │       ├── router.py         ← GET /admin/users, PATCH /admin/users/{id}, POST /admin/reindex
│   │   │       └── service.py        ← AdminService: user management, reindex trigger
│   │   │
│   │   ├── services/                 ← Shared infrastructure services
│   │   │   ├── embedding_service.py  ← EmbeddingService (sentence-transformers, local)
│   │   │   ├── vector_service.py     ← VectorService (ChromaDB CRUD + search)
│   │   │   ├── llm_service.py        ← BaseLLMProvider + GroqProvider + HuggingFaceProvider
│   │   │   ├── document_processor.py ← Parse PDF/DOCX/MD → List[Chunk]
│   │   │   └── storage_service.py    ← S3 upload, download, presign URL
│   │   │
│   │   └── pipeline/
│   │       ├── ingestion_pipeline.py ← Orchestrator: S3→parse→chunk→embed→ChromaDB
│   │       └── rag_pipeline.py       ← Orchestrator: query→embed→search→LLM→stream
│   │
│   ├── tests/
│   │   ├── conftest.py               ← fixtures, mock DynamoDB, mock ChromaDB, test client
│   │   ├── unit/
│   │   │   ├── test_document_processor.py  ← chunk splitting logic
│   │   │   ├── test_embedding_service.py   ← embedding shape/type assertions
│   │   │   ├── test_llm_service.py         ← provider switching, prompt building
│   │   │   ├── test_rag_pipeline.py        ← RAG flow with mocked services
│   │   │   └── test_security.py            ← JWT sign/verify, bcrypt round-trip
│   │   └── integration/
│   │       ├── test_auth.py          ← login, refresh, me, unauthorized access
│   │       ├── test_documents.py     ← upload, status polling, delete
│   │       ├── test_chat.py          ← session CRUD, message, SSE stream
│   │       └── test_admin.py         ← user list, role update, reindex
│   │
│   ├── pyproject.toml                ← ruff + mypy + bandit + pytest config
│   └── requirements.txt
│
├── frontend/                         ← Next.js 14 (App Router, TypeScript)
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/login/page.tsx
│   │   │   ├── chat/page.tsx
│   │   │   └── admin/
│   │   │       ├── page.tsx          ← Document management
│   │   │       └── users/page.tsx    ← User management (admin only)
│   │   ├── components/
│   │   │   ├── ChatMessage.tsx       ← Renders user/assistant messages + sources
│   │   │   ├── SourceCard.tsx        ← Collapsible source document reference
│   │   │   ├── UploadDropzone.tsx    ← Drag-and-drop file upload
│   │   │   ├── DocumentTable.tsx     ← List docs with status badges
│   │   │   └── Sidebar.tsx           ← Chat session list
│   │   └── lib/
│   │       ├── api.ts                ← Typed API client (fetch wrapper)
│   │       └── auth.ts               ← JWT storage, refresh logic
│   └── package.json
│
├── knowledge_base/
│   ├── scripts/
│   │   └── seed_knowledge_base.py    ← Download SBP + HBL public documents
│   └── raw_docs/                     ← Downloaded PDFs land here
│       ├── sbp/                      ← SBP regulatory documents
│       └── hbl/                      ← HBL annual/quarterly reports
│
├── .pre-commit-config.yaml           ← All hooks (ruff, mypy, bandit, detect-secrets…)
├── docker-compose.yml                ← Local: api + frontend + chromadb + dynamodb-local
├── Makefile                          ← dev, test, lint, tf-plan/apply shortcuts
├── .env.example                      ← All env vars documented
├── PROJECT_PLAN.md                   ← THIS FILE
└── README.md
```

---

## 4. Branch & Environment Strategy

### Branch Rules

| Branch | Purpose | Protection Rules | Auto Deploy |
|--------|---------|-----------------|-------------|
| `feature/KMS-{ticket}` | Active development | None | Local only |
| `staging` | Integration / QA | 1 approval required | ✅ ECS staging on merge |
| `main` | Production | 2 approvals + passing CI | ✅ ECS prod (approval gate) |
| `infrastructure` | Terraform changes only | 1 approval required | Plan auto, Apply manual |

### Git Flow

```
feature/KMS-42-chat-streaming
         │
         ▼ Pull Request → 1 review → merge
       staging  ──── auto deploy ──→  AWS Staging
         │
         ▼ Pull Request → 2 reviews → merge
        main  ──── manual approval ──→  AWS Production
```

### Commit Message Convention (enforced by commitizen)
```
feat(chat): add SSE streaming for LLM responses
fix(auth): handle expired refresh token edge case
docs(plan): update API contract for /documents endpoint
chore(deps): update sentence-transformers to 2.7.0
test(integration): add chat session CRUD tests
infra(ecs): increase fargate task memory to 1GB
```

---

## 5. Knowledge Base Design (Two-Layer)

### Layer 1: SBP Regulatory Documents (Domain Knowledge)
- **Source:** `sbp.org.pk` — public domain, no auth
- **Content:** Prudential Regulations, AML/CFT, core banking laws
- **Format:** PDF
- **Purpose:** Answers "What does the regulation say?" questions
- **12 documents** — see `knowledge_base/scripts/seed_knowledge_base.py`

### Layer 2: HBL Public Disclosures (Real Bank Reference)
- **Source:** `hbl.com/assets/documents/` — verified direct links
- **Content:** Annual reports 2021–2024, quarterly reports
- **Format:** PDF
- **Purpose:** Real-world banking operations, financial ratios, product descriptions
- **7 documents** — annual + quarterly reports

### Layer 3: Internal App Documentation (Admin-Uploaded)
- **Source:** Uploaded by admins through the KMS admin panel
- **Content:** SOPs, architecture docs, API guides, runbooks, onboarding docs
- **Format:** PDF, DOCX, MD, TXT
- **Stored in:** S3 bucket → processed and indexed into ChromaDB

### ChromaDB Collection Design

Single collection: `banking_knowledge`

Each chunk document has this metadata:
```json
{
  "doc_id": "uuid",
  "doc_title": "SBP Prudential Regulations for SME",
  "category": "sbp/prudential",
  "layer": "1",
  "source_url": "https://sbp.org.pk/...",
  "page_number": 12,
  "chunk_index": 3,
  "uploaded_by": "system|admin@company.com"
}
```

### Chunking Strategy
- **Chunk size:** 512 tokens (≈ 380 words)
- **Overlap:** 64 tokens (prevents context loss at boundaries)
- **Splitter:** Recursive character splitter (paragraph → sentence → word)
- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` → 384 dimensions

---

## 6. Data Models (DynamoDB Schemas)

> Table names follow pattern: `kms-{environment}-{table}`
> Example: `kms-staging-users`, `kms-prod-chat-messages`

### Table: `kms-{env}-users`

| Field | Type | Description |
|-------|------|-------------|
| `userId` | String (PK) | UUID v4 |
| `email` | String | Unique email — also GSI hash key |
| `hashedPassword` | String | bcrypt hash (cost 12) |
| `role` | String | `admin` or `employee` |
| `isActive` | Boolean | Soft-disable without delete |
| `fullName` | String | Display name |
| `createdAt` | String | ISO 8601 UTC |
| `lastLoginAt` | String | ISO 8601 UTC |

**GSI:** `EmailIndex` — HashKey: `email` — for login lookup

---

### Table: `kms-{env}-documents`

| Field | Type | Description |
|-------|------|-------------|
| `documentId` | String (PK) | UUID v4 |
| `title` | String | Human-readable title |
| `s3Key` | String | `documents/{documentId}/{filename}` |
| `fileType` | String | `pdf`, `docx`, `md`, `txt` |
| `fileSizeBytes` | Number | File size |
| `status` | String | `pending` → `processing` → `ready` → `failed` |
| `failureReason` | String | (optional) error message if `failed` |
| `chunkCount` | Number | Number of chunks in ChromaDB |
| `uploadedBy` | String | userId of uploader |
| `category` | String | `sbp/prudential`, `hbl/annual_reports`, `internal/sop`, etc. |
| `createdAt` | String | ISO 8601 UTC |
| `processedAt` | String | ISO 8601 UTC |

**GSI:** `StatusIndex` — HashKey: `status`
**GSI:** `UploadedByIndex` — HashKey: `uploadedBy`

---

### Table: `kms-{env}-chat-sessions`

| Field | Type | Description |
|-------|------|-------------|
| `userId` | String (PK) | Owner user's ID |
| `sessionId` | String (SK) | UUID v4 |
| `title` | String | Auto-generated from first message (first 60 chars) |
| `createdAt` | String | ISO 8601 UTC |
| `lastMessageAt` | String | ISO 8601 UTC |
| `messageCount` | Number | Running count |

---

### Table: `kms-{env}-chat-messages`

| Field | Type | Description |
|-------|------|-------------|
| `sessionId` | String (PK) | Parent session |
| `messageId` | String (SK) | `{timestamp_ms}#{uuid4_short}` — sorts chronologically |
| `role` | String | `user` or `assistant` |
| `content` | String | Message text |
| `sources` | List | List of `{doc_title, chunk_text, score, category}` |
| `tokensUsed` | Number | LLM tokens consumed (for monitoring) |
| `llmProvider` | String | `groq` or `huggingface` |
| `latencyMs` | Number | End-to-end response time |
| `createdAt` | String | ISO 8601 UTC |

---

## 7. API Contract (All Endpoints)

**Base URL:** `http://localhost:8000/api/v1` (local) | `https://{alb-dns}/api/v1` (deployed)

All endpoints return JSON. Auth endpoints use `Authorization: Bearer {access_token}`.

---

### Auth

#### `POST /api/v1/auth/login`
```json
// Request
{ "email": "user@company.com", "password": "secret" }

// Response 200
{
  "accessToken": "eyJ...",
  "refreshToken": "eyJ...",
  "tokenType": "bearer",
  "expiresIn": 3600,
  "user": { "userId": "uuid", "email": "...", "role": "employee", "fullName": "Alice Khan" }
}

// Response 401
{ "detail": "Invalid credentials" }
```

#### `POST /api/v1/auth/refresh`
```json
// Request
{ "refreshToken": "eyJ..." }

// Response 200
{ "accessToken": "eyJ...", "expiresIn": 3600 }
```

#### `GET /api/v1/auth/me`  *(requires auth)*
```json
// Response 200
{ "userId": "uuid", "email": "...", "role": "employee", "fullName": "Alice Khan", "lastLoginAt": "2026-04-18T10:00:00Z" }
```

---

### Documents

#### `POST /api/v1/documents/upload`  *(requires auth, multipart/form-data)*
```
Fields:
  file:     binary (PDF, DOCX, MD, TXT — max 50MB)
  title:    string (optional, defaults to filename)
  category: string (optional, e.g. "internal/sop")
```
```json
// Response 202 (accepted, processing begins async)
{
  "documentId": "uuid",
  "title": "SBP SME Regulations",
  "status": "pending",
  "message": "Document queued for processing"
}
```

#### `GET /api/v1/documents/`  *(requires auth)*
```json
// Query params: ?status=ready&category=sbp&limit=20&cursor=xxx
// Response 200
{
  "items": [
    {
      "documentId": "uuid",
      "title": "SBP PR SME 2025",
      "status": "ready",
      "chunkCount": 84,
      "fileType": "pdf",
      "fileSizeBytes": 2048000,
      "category": "sbp/prudential",
      "uploadedBy": "system",
      "createdAt": "2026-04-01T08:00:00Z"
    }
  ],
  "nextCursor": "base64encodedkey"
}
```

#### `GET /api/v1/documents/{documentId}`  *(requires auth)*
```json
// Response 200
{
  "documentId": "uuid",
  "title": "SBP PR SME 2025",
  "status": "ready",
  "chunkCount": 84,
  "fileType": "pdf",
  "fileSizeBytes": 819200,
  "category": "sbp/prudential",
  "sourceUrl": "https://sbp.org.pk/...",
  "uploadedBy": "system",
  "createdAt": "2026-04-01T08:00:00Z",
  "processedAt": "2026-04-01T08:02:15Z"
}
```

#### `GET /api/v1/documents/{documentId}/chunks`  *(requires auth)*
```json
// Query: ?limit=20&offset=0
// Returns paginated text chunks — used by KB Preview modal
{
  "documentId": "uuid",
  "title": "SBP PR SME 2025",
  "totalChunks": 84,
  "chunks": [
    {
      "chunkIndex": 0,
      "pageNumber": 1,
      "text": "PRUDENTIAL REGULATIONS FOR SME FINANCING...\n\nPART A - DEFINITIONS..."
    },
    {
      "chunkIndex": 1,
      "pageNumber": 2,
      "text": "1. SME means an entity with annual sales turnover not exceeding PKR 800 million..."
    }
  ],
  "nextOffset": 20
}
```

#### `DELETE /api/v1/documents/{documentId}`  *(requires admin)*
```json
// Response 200
{ "message": "Document deleted", "chunksRemoved": 84 }
```

#### `POST /api/v1/documents/{documentId}/reindex`  *(requires admin)*
```json
// Re-runs ingestion pipeline for a single document
// Useful if re-processing failed or chunking config changed
// Response 202
{ "message": "Reindex queued", "documentId": "uuid" }
```

---

### Chat

#### `POST /api/v1/chat/sessions`  *(requires auth)*
```json
// Request (empty body or optional metadata)
{}

// Response 201
{ "sessionId": "uuid", "userId": "uuid", "createdAt": "..." }
```

#### `POST /api/v1/chat/sessions/{sessionId}/message`  *(requires auth, returns SSE)*
```json
// Request
{
  "question": "What is the SBP provisioning requirement for a Substandard loan?",
  "topK": 5
}
```
```
// Response: text/event-stream (SSE)
event: chunk
data: {"text": "According to SBP Prudential Regulations, "}

event: chunk
data: {"text": "a Substandard loan (180–269 days overdue) requires "}

event: chunk
data: {"text": "25% provisioning of the outstanding balance."}

event: sources
data: {
  "sources": [
    {
      "docTitle": "SBP PR SME 2025",
      "category": "sbp/prudential",
      "chunkText": "Substandard: Where the principal or markup...",
      "score": 0.91,
      "pageNumber": 14
    }
  ]
}

event: done
data: { "latencyMs": 3200, "tokensUsed": 412, "provider": "groq" }
```

#### `GET /api/v1/chat/sessions/`  *(requires auth)*
```json
// Returns current user's sessions, sorted by lastMessageAt desc
// Query: ?limit=20&cursor=xxx
{
  "sessions": [
    { "sessionId": "uuid", "title": "SBP provisioning requirement for...", "messageCount": 4, "lastMessageAt": "..." }
  ]
}
```

#### `GET /api/v1/chat/sessions/{sessionId}/messages`  *(requires auth)*
```json
// Returns all messages in a session
{
  "messages": [
    { "messageId": "...", "role": "user", "content": "...", "createdAt": "..." },
    { "messageId": "...", "role": "assistant", "content": "...", "sources": [...], "createdAt": "..." }
  ]
}
```

---

### Admin

#### `GET /api/v1/admin/users`  *(requires admin)*
#### `POST /api/v1/admin/users`  *(requires admin — create user)*
#### `PATCH /api/v1/admin/users/{userId}`  *(requires admin — update role/isActive)*
#### `POST /api/v1/admin/reindex`  *(requires admin — re-process all documents)*

---

### Health

#### `GET /health`  *(no auth — used by ALB health checks)*
```json
{ "status": "ok", "version": "1.0.0", "environment": "staging" }
```

---

## 8. Core Service Interfaces

> All services are Python classes. These interfaces define the contract.
> Each developer building a service must implement these exact method signatures.

### EmbeddingService
```python
class EmbeddingService:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of texts. Returns list of 384-dim vectors.
        Uses sentence-transformers/all-MiniLM-L6-v2 (local, free).
        """

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string. Returns 384-dim vector."""
```

### VectorService
```python
class VectorService:
    def upsert_chunks(
        self, doc_id: str, chunks: list[str], embeddings: list[list[float]], metadata: list[dict]
    ) -> int:
        """Store chunks in ChromaDB. Returns number of chunks stored."""

    def search_similar(
        self, query_embedding: list[float], top_k: int = 5, where: dict | None = None
    ) -> list[SearchResult]:
        """Return top_k most similar chunks with metadata and score."""

    def delete_document(self, doc_id: str) -> int:
        """Delete all chunks for a document. Returns count deleted."""
```

### BaseLLMProvider (abstract)
```python
class BaseLLMProvider(ABC):
    @abstractmethod
    async def chat_stream(
        self, question: str, context_chunks: list[str], chat_history: list[dict]
    ) -> AsyncGenerator[str, None]:
        """Stream answer tokens given question + retrieved context chunks."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return 'groq' or 'huggingface'."""
```

### DocumentProcessor
```python
class DocumentProcessor:
    def process(self, file_path: Path, file_type: str) -> list[Chunk]:
        """
        Parse file and split into chunks.
        Supports: pdf (pypdf), docx (python-docx), md/txt (plain text).
        Returns list of Chunk(content: str, metadata: dict).
        Chunk size: 512 tokens, overlap: 64 tokens.
        """
```

### IngestionPipeline
```python
class IngestionPipeline:
    async def run(self, document_id: str) -> IngestionResult:
        """
        Full pipeline:
        1. Fetch raw file from S3
        2. Parse with DocumentProcessor
        3. Generate embeddings with EmbeddingService
        4. Store in ChromaDB via VectorService
        5. Update DynamoDB document status
        Returns: IngestionResult(chunk_count, status, error_message)
        """
```

### RAGPipeline
```python
class RAGPipeline:
    async def query_stream(
        self, question: str, session_id: str, top_k: int = 5
    ) -> AsyncGenerator[RAGEvent, None]:
        """
        Full RAG:
        1. Embed question with EmbeddingService
        2. Search ChromaDB via VectorService → top_k chunks
        3. Build prompt: system_prompt + context + chat_history
        4. Stream answer through LLMProvider
        5. Yield RAGEvent (chunk text | sources | done)
        """
```

---

## 9. Key System Flows (Sequence Diagrams)

### Flow 1: Employee Asks a Question

```
Employee (Browser)    Frontend       API           VectorService   LLMProvider
     │                   │            │                 │               │
     │──POST /message──→ │            │                 │               │
     │                   │──POST /chat/sessions/{id}/message──────────→ │
     │                   │            │                 │               │
     │                   │            │──embed(question)─────────────→  │
     │                   │            │←────────────────vector(384d)──  │
     │                   │            │                 │               │
     │                   │            │──search(vector, top_k=5)──────→ │
     │                   │            │←────────────────[chunks+meta]── │
     │                   │            │                 │               │
     │                   │            │──stream(question + chunks)────────────────→
     │                   │            │                 │               │
     │←─────────SSE stream (text chunks)────────────────────────────────│
     │                   │←─────────SSE stream──────── │               │
     │                   │            │                 │               │
     │←─────────SSE event: sources─── │                │               │
     │                   │            │──save(Q+A to DynamoDB)          │
     │←─────────SSE event: done────── │                │               │
```

### Flow 2: Admin Uploads a Document

```
Admin (Browser)      Frontend       API           S3          DynamoDB      ChromaDB
     │                  │            │             │              │              │
     │──Upload PDF───→  │            │             │              │              │
     │                  │──POST /documents/upload──────────────→  │              │
     │                  │            │─────────────upload file──→ │              │
     │                  │            │←─────────────s3Key─────── │              │
     │                  │            │──put_item(status=pending)──────────────→  │
     │←─202 Accepted────│←────────── │             │              │              │
     │                  │            │                            │              │
     │                  │   [BackgroundTask starts]               │              │
     │                  │            │─────────────get file────→  │              │
     │                  │            │──update(status=processing)─────────────→  │
     │                  │            │──parse PDF → chunks        │              │
     │                  │            │──embed chunks              │              │
     │                  │            │──────────────────────────────────upsert──→
     │                  │            │──update(status=ready, chunkCount=N)─────→ │
     │                  │            │             │              │              │
     │ (polls GET /documents/{id} every 3s)        │              │              │
     │←─status: ready───│            │             │              │              │
```

---

## 10. Infrastructure (Terraform)

### AWS Resources Per Environment

| Resource | Staging | Prod |
|----------|---------|------|
| VPC | 1 (2 public + 2 private subnets, 1 NAT GW) | Same |
| ECS Cluster | 1 Fargate (standard) | 1 Fargate (standard) |
| ECS Tasks | 1× API (0.25vCPU, 0.5GB) | 2× API (0.5vCPU, 1GB) |
| ALB | 1 | 1 |
| DynamoDB | 4 tables (PAY_PER_REQUEST, no PITR) | 4 tables (PAY_PER_REQUEST, PITR on) |
| S3 | 1 bucket (30-day lifecycle to IA) | 1 bucket (90-day lifecycle to Glacier) |
| ECR | 2 repos (api, frontend) — shared | Same repos, tagged differently |
| IAM | Task exec role, task role, OIDC role | Same |
| EFS | 1 mount (ChromaDB volume) | 1 mount |

### Terraform Module Inputs/Outputs Summary

```
module "vpc"
  inputs:  project_name, environment, vpc_cidr, az_count
  outputs: vpc_id, public_subnet_ids, private_subnet_ids, alb_sg_id, ecs_sg_id

module "ecs"
  inputs:  project_name, environment, vpc_id, subnets, sg_ids, api_image, api_cpu/mem, desired_count, env_vars
  outputs: cluster_name, alb_dns_name, api_service_name

module "dynamodb"
  inputs:  project_name, environment, enable_pitr
  outputs: *_table_name, *_table_arn (for all 4 tables)

module "s3"
  inputs:  project_name, environment, lifecycle_glacier_days
  outputs: bucket_name, bucket_arn

module "iam"
  inputs:  project_name, environment, s3_bucket_arn, dynamodb_table_arns, github_org, github_repo
  outputs: task_execution_role_arn, task_role_arn, deploy_role_arn
```

### Remote State
- **Backend:** S3 bucket `kms-terraform-state` + DynamoDB lock table `kms-terraform-locks`
- **State paths:**
  - `staging/terraform.tfstate`
  - `prod/terraform.tfstate`

---

## 11. CI/CD Pipelines (GitHub Actions)

### `ci.yml` — Runs on every push and PR

```yaml
Trigger: push to any branch, pull_request to staging or main

Steps:
  1. Checkout code
  2. Setup Python 3.11 (cached pip)
  3. pip install -r backend/requirements.txt
  4. pre-commit run --all-files
     ├── ruff check + format
     ├── mypy (type checking)
     ├── bandit (security scan)
     ├── detect-secrets (no leaked keys)
     └── terraform fmt check
  5. pytest tests/unit/ -v --cov=app --cov-report=xml
  6. Upload coverage to Codecov
  7. Report status check (required for PR merge)
```

### `staging.yml` — Deploy to staging

```yaml
Trigger: push to staging branch (after PR merge)

Steps:
  1. Run ci.yml jobs (reused)
  2. Configure AWS credentials via OIDC (no long-lived keys)
     Role: arn:aws:iam::{account}:role/kms-staging-github-deploy
  3. docker build --target production -f infrastructure/docker/Dockerfile.api
  4. docker tag kms-api:staging-{sha}
  5. docker push to ECR
  6. aws ecs update-service --cluster kms-staging-cluster --force-new-deployment
  7. Wait for service stability (60s timeout)
  8. Run integration smoke tests: pytest tests/integration/ -m smoke
```

### `prod.yml` — Deploy to production

```yaml
Trigger: push to main branch

Steps:
  1. Run ci.yml jobs (reused)
  2. [MANUAL APPROVAL GATE] — GitHub Environment "production"
     Required reviewers: 1 senior engineer + 1 team lead
  3. Configure AWS credentials via OIDC
     Role: arn:aws:iam::{account}:role/kms-prod-github-deploy
  4. docker build --target production
  5. docker tag kms-api:prod-{sha} AND kms-api:prod-latest
  6. docker push to ECR
  7. aws ecs update-service --cluster kms-prod-cluster --force-new-deployment
  8. Wait 90s for stability
  9. Run health check: curl https://{prod-alb}/health
 10. Notify Slack on success or failure
```

### `terraform.yml` — Infrastructure changes

```yaml
Trigger: push to infrastructure branch

Steps:
  1. terraform fmt --check (all modules)
  2. terraform init + terraform validate (staging env)
  3. terraform init + terraform validate (prod env)
  4. terraform plan -out=staging.tfplan (staging)
  5. Upload plan as PR artifact + comment plan diff on PR
  6. [MANUAL] terraform apply — triggered via workflow_dispatch after PR review
```

---

## 12. Code Quality & Pre-commit Hooks

All hooks run automatically on `git commit`. CI also runs them.

| Hook | Tool | What It Catches |
|------|------|----------------|
| Trailing whitespace | pre-commit-hooks | Formatting noise |
| End of file fixer | pre-commit-hooks | Missing newline |
| YAML/JSON/TOML check | pre-commit-hooks | Syntax errors |
| Large file check | pre-commit-hooks | Blocks files >500KB |
| **Detect private key** | pre-commit-hooks | AWS keys, SSH keys in code |
| **Ruff lint** | ruff | PEP8, unused imports, bad patterns |
| **Ruff format** | ruff | Consistent code formatting |
| **Mypy** | mypy | Type errors, missing annotations |
| **Bandit** | bandit | SQL injection, hardcoded passwords, weak crypto |
| **detect-secrets** | Yelp detect-secrets | API keys, tokens, passwords in any file |
| **Safety** | safety | Known CVEs in requirements.txt |
| **Hadolint** | hadolint | Dockerfile best practices + security |
| **Terraform fmt** | terraform | HCL formatting |
| **Commitizen** | commitizen | Conventional commit message format |

### Setup for Developers
```bash
pip install pre-commit
pre-commit install          # installs git hooks
pre-commit install --hook-type commit-msg  # installs commit-msg hook
pre-commit run --all-files  # run manually on all files
```

---

## 13. Testing Strategy

### Unit Tests (`tests/unit/`) — No external dependencies

| File | What to Test |
|------|-------------|
| `test_document_processor.py` | PDF parsing, chunking size, overlap, special chars |
| `test_embedding_service.py` | Output shape (384d), batch sizing, determinism |
| `test_llm_service.py` | Provider switching via env var, prompt construction, mock stream |
| `test_rag_pipeline.py` | Context assembly, source deduplication, empty results handling |
| `test_security.py` | JWT sign/verify, expiry, bcrypt hash/verify, role validation |

**Run:** `pytest tests/unit/ -v`
**Coverage target:** ≥ 80%

### Integration Tests (`tests/integration/`) — Real DynamoDB Local + ChromaDB in Docker

| File | Endpoints Covered |
|------|------------------|
| `test_auth.py` | Login success/fail, token refresh, /me auth |
| `test_documents.py` | Upload → status pending → ready, delete, list |
| `test_chat.py` | Create session, send message (mocked LLM), get history |
| `test_admin.py` | User CRUD, role update, reindex trigger |

**Run:** `docker-compose up -d && pytest tests/integration/ -v`

### Test Fixtures (conftest.py)
```python
# Key fixtures every developer must know:
@pytest.fixture  client           # TestClient(app) with auth headers
@pytest.fixture  dynamo_tables    # created DynamoDB Local tables (cleaned after each test)
@pytest.fixture  chroma_client    # in-memory ChromaDB client
@pytest.fixture  mock_llm         # returns predictable chunks, no real API call
@pytest.fixture  admin_user       # pre-seeded admin user + JWT token
@pytest.fixture  employee_user    # pre-seeded employee user + JWT token
```

---

## 14. Environment Variables Reference

```env
# ── App ──────────────────────────────────────────────────────
ENVIRONMENT=development          # development | staging | production
SECRET_KEY=<32-byte hex>         # generate: openssl rand -hex 32
CORS_ORIGINS=http://localhost:3000

# ── AWS ──────────────────────────────────────────────────────
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<key>          # not needed in ECS (task role used)
AWS_SECRET_ACCESS_KEY=<secret>   # not needed in ECS (task role used)
S3_BUCKET_NAME=kms-documents-dev

# ── DynamoDB ─────────────────────────────────────────────────
DYNAMODB_ENDPOINT_URL=http://localhost:8001   # LOCAL ONLY — remove in AWS
TABLE_USERS=kms-development-users
TABLE_DOCUMENTS=kms-development-documents
TABLE_CHAT_SESSIONS=kms-development-chat-sessions
TABLE_CHAT_MESSAGES=kms-development-chat-messages

# ── ChromaDB ─────────────────────────────────────────────────
CHROMA_HOST=chromadb             # service name in docker-compose
CHROMA_PORT=8000
CHROMA_COLLECTION=banking_knowledge

# ── LLM Provider ─────────────────────────────────────────────
LLM_PROVIDER=groq                # groq | huggingface
LLM_MODEL_NAME=llama-3.1-70b-versatile
GROQ_API_KEY=gsk_xxx             # free: console.groq.com
HUGGINGFACE_API_KEY=hf_xxx       # free: huggingface.co/settings/tokens

# ── Embeddings ───────────────────────────────────────────────
EMBEDDING_PROVIDER=local         # local (free) | openai
# OPENAI_API_KEY=sk-...          # only if EMBEDDING_PROVIDER=openai

# ── JWT ──────────────────────────────────────────────────────
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# ── Seed Admin ───────────────────────────────────────────────
ADMIN_EMAIL=admin@company.com    # created on first startup
ADMIN_PASSWORD=change-me-now
```

---

## 15. Local Development Setup

### Prerequisites
- Docker Desktop (or Docker Engine + Compose)
- Python 3.11+
- Node.js 20+
- Git
- Terraform 1.6+ (for infra work only)

### First-Time Setup
```bash
# 1. Clone repo
git clone https://github.com/your-org/kms.git
cd kms

# 2. Copy env file and fill in your API keys
cp .env.example .env
# Edit: set GROQ_API_KEY and ADMIN_PASSWORD at minimum

# 3. Install pre-commit hooks
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg

# 4. Start all services
docker compose up --build

# Services available at:
#   API:            http://localhost:8000
#   API Docs:       http://localhost:8000/docs
#   Frontend:       http://localhost:3000
#   DynamoDB Admin: http://localhost:8888
#   ChromaDB:       http://localhost:8002

# 5. Create DynamoDB tables (local)
docker compose exec api python -m app.core.dynamo_init

# 6. Download knowledge base documents (optional but recommended)
pip install httpx
python knowledge_base/scripts/seed_knowledge_base.py

# 7. Ingest knowledge base (after download completes)
curl -X POST http://localhost:8000/api/v1/admin/reindex \
  -H "Authorization: Bearer $(curl -s -X POST http://localhost:8000/api/v1/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"email":"admin@company.com","password":"change-me-now"}' | jq -r .accessToken)"

# 8. Run tests
make test-unit        # fast, no deps
make test-integration # requires docker-compose up
```

---

## 16. Frontend Pages & Components

### Pages

| Route | Auth | Description |
|-------|------|-------------|
| `/login` | Public | Email + password form |
| `/chat` | Employee | Main chat interface — the only page employees use |
| `/admin` | **Admin only** | Knowledge base management: browse, preview, add, delete, reindex |
| `/admin/users` | **Admin only** | User management |

### Knowledge Base Access Model

| Action | Employee | Admin |
|--------|----------|-------|
| Use chat (ask questions) | ✅ | ✅ |
| Browse / list documents in KB | ❌ | ✅ |
| Search documents by title/category | ❌ | ✅ |
| Preview document chunks (scroll) | ❌ | ✅ |
| Upload / add new documents | ❌ | ✅ |
| Delete documents | ❌ | ✅ |
| Reindex a document | ❌ | ✅ |
| Manage users (create, role, disable) | ❌ | ✅ |

### Key Component Behaviours

**`ChatMessage.tsx`**
- Renders user message (right-aligned, blue)
- Renders assistant message (left-aligned, white) with markdown
- Streams text character-by-character as SSE chunks arrive
- Shows "Thinking..." spinner during first chunk delay
- Renders `SourceCard` components after text completes

**`SourceCard.tsx`**
- Collapsible card showing: doc title, category badge, relevance score (0–1), excerpt
- Click to expand chunk text

**`KBDocumentTable.tsx`** *(Admin — Knowledge Base Browser)*
- Paginated table of all documents — **admin view only**
- Columns: Title, Category, Status badge, Chunk Count, File Type, Uploaded By, Date
- Filter bar: filter by category (SBP/HBL/Internal), status, file type
- Search bar: searches document titles (client-side filter)
- Each row: **Preview** button → opens `KBDocumentPreview` modal, **Delete** (with confirmation dialog), **Re-index** button

**`KBDocumentPreview.tsx`** *(Admin — Chunk Viewer)*
- Modal/panel that opens on Preview click (admin only)
- Shows document metadata at top (title, category, source URL if public, processed date)
- Scrollable list of all text chunks for that document
- Each chunk shows: chunk index, page number (if PDF), chunk text (truncated to 3 lines, expand on click)
- Allows admin to verify indexed content quality before employees use the chat

**`UploadDropzone.tsx`**
- Accepts: PDF, DOCX, MD, TXT — max 50MB
- Shows: upload progress bar, file name, cancel button
- On complete: polls `GET /documents/{id}` every 3 seconds
- Shows status badge: `pending` → `processing` → `ready` or `failed` with error

**`Sidebar.tsx`**
- Lists all user's chat sessions sorted by most recent
- "New Chat" button creates a new session
- Active session highlighted
- Each session shows auto-generated title (first 60 chars of first message)

---

## 17. Deployment Guide

### First-Time AWS Setup (one-off)

```bash
# 1. Bootstrap Terraform remote state (run once)
cd infrastructure/terraform
terraform init -backend=false
terraform apply -target=aws_s3_bucket.terraform_state \
               -target=aws_s3_bucket_versioning.terraform_state \
               -target=aws_dynamodb_table.terraform_locks

# 2. Create ECR repositories (one-off)
aws ecr create-repository --repository-name kms-api
aws ecr create-repository --repository-name kms-frontend

# 3. Apply staging infrastructure
make tf-init-staging
make tf-plan-staging   # review output
make tf-apply-staging
```

### Deploy New Feature
```bash
# Developer flow:
git checkout -b feature/KMS-{ticket}-{description}
# ... make changes, commit with conventional format ...
git push origin feature/KMS-{ticket}
# Open PR → staging branch
# CI runs automatically
# After approval, merge → auto-deploys to staging
# QA verifies on staging
# Open PR → main
# 2 approvals required
# GitHub Actions pauses for deployment approval
# Approve → auto-deploys to prod
```

---

## Appendix: Cost Estimate

| Resource | Staging/mo | Prod/mo |
|----------|-----------|---------|
| ECS Fargate (standard) | ~$12 | ~$24 |
| ALB | ~$18 | ~$18 |
| NAT Gateway (1 AZ) | ~$5 | ~$10 |
| DynamoDB (PAY_PER_REQUEST) | ~$0–3 | ~$3–8 |
| EFS (ChromaDB volume) | ~$1 | ~$2 |
| S3 (10GB) | ~$0.25 | ~$0.25 |
| **Total** | **~$36–39** | **~$57–62** |

> LLM (Groq free tier) = **$0** · Embeddings (local) = **$0**

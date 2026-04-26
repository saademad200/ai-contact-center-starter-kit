# AI Contact Centre for Investment Banking
## Complete Project Plan — Team Reference Document

**Domain:** Al Meezan Investments (Pakistan's largest Islamic asset management company)
**Version:** 1.0 | **Date:** April 2026
**Audience:** All engineering team members, QA, DevOps

> An AI-powered customer support agent for an investment management company.
> Customers interact via a website chat widget. The AI agent uses **tool calling**
> (not just RAG) to answer questions about funds, NAVs, performance, risk profiling,
> and account services — escalating to human agents when needed.

---

## Table of Contents

1. [Problem & Solution](#1-problem--solution)
2. [System Architecture](#2-system-architecture)
3. [AI Agent — Tool Calling Design](#3-ai-agent--tool-calling-design)
4. [Knowledge Base (Al Meezan + SECP + MUFAP)](#4-knowledge-base)
5. [Data Models (DynamoDB Schemas)](#5-data-models-dynamodb-schemas)
6. [API Contract (All Endpoints)](#6-api-contract-all-endpoints)
7. [Chat Widget (Embeddable JS)](#7-chat-widget-embeddable-js)
8. [Admin Panel (Web UI)](#8-admin-panel-web-ui)
9. [MLOps Pipeline](#9-mlops-pipeline)
10. [Repository Structure](#10-repository-structure)
11. [Infrastructure (Terraform Guide)](#11-infrastructure-terraform-guide)
12. [CI/CD Pipelines (GitHub Actions)](#12-cicd-pipelines-github-actions)
13. [Code Quality & Pre-commit Hooks](#13-code-quality--pre-commit-hooks)
14. [Testing Strategy](#14-testing-strategy)
15. [Environment Variables Reference](#15-environment-variables-reference)
16. [Local Development Setup](#16-local-development-setup)


---

## 1. Problem & Solution

### Problem
Al Meezan Investments receives thousands of customer queries monthly across phone, email, and walk-ins. Most questions are repetitive:
- "What's the current NAV of Meezan Islamic Fund?"
- "Which fund is best for my risk profile?"
- "How do I open an account?"
- "What's my fund's YTD return?"
- "Is this fund Shariah-compliant?"


### Solution
An AI agent embedded as a chat widget on the Al Meezan website. Instead of simple Q&A, the agent has **tools** it can invoke:

| Customer says | Agent action | Tool invoked |
|---------------|-------------|-------------|
| "What's the NAV of Meezan Islamic Fund?" | Looks up current NAV | `get_fund_nav` |
| "Compare MIF vs MIIF" | Generates comparison table | `compare_funds` |
| "I'm 30, moderate income, 15-year horizon" | Runs risk assessment | `assess_risk_profile` |
| "How do I open a digital account?" | Searches knowledge base | `search_knowledge_base` |
| "I need to speak to someone about my complaint" | Creates ticket, routes to agent | `escalate_to_human` |
| "What are the tax implications of CGT?" | Searches SECP regulations | `search_knowledge_base` |

### Non-Goals (v1)
- Real-time NAV from live API (we use daily-refreshed data from MUFAP)
- Account login / portfolio view (requires core banking integration)
- Transaction execution (buy/sell/switch)
- Multi-language (English only)

### Success Criteria
- 60% of queries auto-resolved without human agent
- Response time < 8 seconds including tool call
- Risk profiling conversation completes in < 5 exchanges
- Admin can add new FAQ document → searchable within 5 minutes

---

## 2. System Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                Customer (Browser)                                 │
│  <script src="https://yourcdn/widget.js"></script>                │
│  Chat widget appears bottom-right of any page                     │
└───────────────────────────┬──────────────────────────────────────┘
                            │ WebSocket (wss://)
                ┌───────────▼───────────┐
                │     API Service       │
                │  FastAPI + WebSocket  │
                │  ECS Fargate          │
                └───────────┬───────────┘
                            │
              ┌─────────────┼──────────────────────┐
              │             │                      │
              ▼             ▼                      ▼
     ┌────────────┐  ┌────────────┐   ┌────────────────────┐
     │ AI Agent   │  │ DynamoDB   │   │    ChromaDB        │
     │ (Groq LLM  │  │ (metadata  │   │  (vector store)    │
     │  + Tools)  │  │  + tickets │   │  ECS + EFS volume  │
     └─────┬──────┘  │  + convos) │   └────────────────────┘
           │         └────────────┘
           │ Tool calls
     ┌─────┼─────────────────────────────────┐
     │     │              │                   │
     ▼     ▼              ▼                   ▼
 ┌──────┐ ┌──────────┐ ┌────────────┐ ┌────────────┐
 │search│ │get_nav   │ │risk_profile│ │ escalate   │
 │  KB  │ │compare   │ │            │ │ to human   │
 │(RAG) │ │fund_perf │ │            │ │(DynamoDB)  │
 └──────┘ └──────────┘ └────────────┘ └────────────┘

     ┌────────────────────┐
     │  Admin Panel       │
     │  (FastAPI + HTML)  │
     │  KB + Tickets +    │
     │  Quality Dashboard │
     └────────────────────┘
```

### Component Responsibilities

| Component | Technology | Responsibility |
|-----------|-----------|----------------|
| **API Service** | FastAPI, ECS Fargate | WebSocket chat, REST API, agent orchestration, auth |
| **AI Agent** | Groq API (Llama 3.1 70B) | Tool calling, intent detection, response generation |
| **Chat Widget** | Vanilla JS (embeddable) | Customer-facing chat interface |
| **Admin Panel** | FastAPI + Jinja2 templates | KB management, ticket review, quality dashboard |
| **ChromaDB** | ChromaDB container, EFS | Vector store for knowledge base |
| **DynamoDB** | AWS DynamoDB (PAY_PER_REQUEST) | Conversations, tickets, users, documents metadata |
| **S3** | AWS S3 | Raw uploaded documents |
| **Embeddings** | sentence-transformers (local) | 384-dim vectors, runs on Fargate CPU |
| **AWS SES** | AWS Simple Email Service | Ticket confirmations, resolution emails, deploy alerts |

---

## 3. AI Agent — Tool Calling Design

### How Tool Calling Works

Groq's Llama 3.1 70B supports native tool/function calling. The LLM doesn't just generate text — it decides **which tool(s) to invoke** based on the customer's message, calls them, gets results, and then generates a natural language response incorporating the tool output.

```
Customer: "What's the current NAV of Meezan Islamic Fund and how has it performed this year?"

LLM thinks: I need two tools — get_fund_nav and get_fund_performance

Tool call 1: get_fund_nav(fund_name="Meezan Islamic Fund")
→ Returns: { nav: 45.23, date: "2026-04-25", currency: "PKR" }

Tool call 2: get_fund_performance(fund_name="Meezan Islamic Fund", period="ytd")
→ Returns: { ytd: 18.5, mtd: 2.1, "1y": 22.3, "3y": 45.7 }

LLM generates: "The current NAV of Meezan Islamic Fund is PKR 45.23 (as of April 25, 2026).
Year-to-date, the fund has returned 18.5%, and its 1-year return is 22.3%.
Would you like me to compare this with other equity funds?"
```

### Tool Definitions

Each tool is a Python function the agent can invoke. The LLM receives the function schema (name, description, parameters) and decides when to call it.

---

#### Tool 1: `search_knowledge_base`
```python
def search_knowledge_base(query: str, category: str | None = None, top_k: int = 5) -> list[dict]:
    """
    Search the Al Meezan knowledge base using semantic similarity (RAG).
    Use this for general questions about account opening, processes, Shariah compliance,
    SECP regulations, fee structures, and any procedural queries.

    Args:
        query: The customer's question in natural language
        category: Optional filter — "faq", "fund_docs", "secp", "process"
        top_k: Number of relevant chunks to return (default 5)

    Returns:
        List of { text, source_document, page_number, score }
    """
```

**When LLM should use this:** Account opening, KYC process, Shariah compliance, tax rules, fee structures, general FAQs — anything factual that's in the knowledge base documents.

---

#### Tool 2: `get_fund_nav`
```python
def get_fund_nav(fund_name: str) -> dict:
    """
    Get the latest Net Asset Value (NAV) for an Al Meezan fund.
    NAV data is refreshed daily from MUFAP.

    Args:
        fund_name: Full or partial fund name (e.g. "Meezan Islamic Fund" or "MIF")

    Returns:
        { fund_name, ticker, nav, nav_date, fund_category, management_fee_pct }
    """
```

**When LLM should use this:** "What's the NAV of...", "How much is one unit of...", "current price of..."

**Data source:** MUFAP daily NAV table, stored in DynamoDB `funds` table, refreshed daily via a scheduled Lambda or ECS scheduled task.

---

#### Tool 3: `get_fund_performance`
```python
def get_fund_performance(fund_name: str, period: str = "all") -> dict:
    """
    Get performance metrics for an Al Meezan fund.

    Args:
        fund_name: Full or partial fund name
        period: "1d", "1w", "1m", "3m", "6m", "ytd", "1y", "3y", "5y", or "all"

    Returns:
        { fund_name, ticker, returns: { "1d": 0.1, "1m": 1.2, "ytd": 18.5, ... },
          benchmark, category_avg, fund_rating, risk_level }
    """
```

**When LLM should use this:** "How has... performed?", "What's the return on...", "Is MIF doing better than..."

---

#### Tool 4: `compare_funds`
```python
def compare_funds(fund_names: list[str], metrics: list[str] | None = None) -> dict:
    """
    Compare 2-4 Al Meezan funds side-by-side.

    Args:
        fund_names: List of 2-4 fund names to compare
        metrics: Optional list of specific metrics — defaults to all
                 Options: "nav", "returns", "risk", "fees", "category", "rating"

    Returns:
        { comparison_table: [ { fund_name, nav, ytd, 1y, 3y, risk_level, fee, rating } ] }
    """
```

**When LLM should use this:** "Compare MIF and MIIF", "Which equity fund is better?", "Difference between..."

---

#### Tool 5: `assess_risk_profile`
```python
def assess_risk_profile(
    age: int,
    monthly_income_pkr: int,
    investment_horizon_years: int,
    risk_tolerance: str,  # "low", "medium", "high"
    existing_investments: str | None = None,
    investment_goal: str | None = None
) -> dict:
    """
    Assess investor's risk profile and suggest fund allocation.
    Based on SECP investor suitability guidelines.

    Args:
        age: Investor's age
        monthly_income_pkr: Monthly income in PKR
        investment_horizon_years: How long they plan to invest
        risk_tolerance: Self-assessed risk tolerance
        existing_investments: Description of current investments (optional)
        investment_goal: "retirement", "education", "wealth_growth", "income" (optional)

    Returns:
        {
          risk_profile: "Conservative" | "Moderate" | "Aggressive",
          risk_score: 1-10,
          suggested_allocation: {
            "equity": 20, "income": 50, "money_market": 30
          },
          recommended_funds: [
            { name: "Meezan Islamic Fund", allocation_pct: 20, reason: "..." },
            { name: "Meezan Islamic Income Fund", allocation_pct: 50, reason: "..." },
            { name: "Meezan Cash Fund", allocation_pct: 30, reason: "..." }
          ],
          disclaimer: "This is for informational purposes only..."
        }
    """
```

**When LLM should use this:** The LLM first asks the customer a series of questions (age, income, horizon, risk tolerance) through conversation, then calls this tool with collected data. This creates a **guided multi-turn conversation**.

**Example conversation:**
```
Customer: "I want to invest, which fund should I choose?"
Agent: "I'd be happy to help! Let me understand your profile first.
        How old are you and what's your approximate monthly income?"
Customer: "I'm 32, I earn about PKR 200,000 per month"
Agent: "Great. How long do you plan to stay invested? And would you say
        your risk tolerance is low, medium, or high?"
Customer: "10 years, medium risk I'd say"
Agent: [calls assess_risk_profile(age=32, monthly_income_pkr=200000,
        investment_horizon_years=10, risk_tolerance="medium")]
Agent: "Based on your profile, you have a **Moderate** risk profile (score: 6/10).
        Here's a suggested allocation:
        • 40% Equity → Meezan Islamic Fund (MIF) — strong long-term growth
        • 40% Income → Meezan Islamic Income Fund (MIIF) — stable returns
        • 20% Money Market → Meezan Cash Fund (MCF) — liquidity buffer
        ⚠️ This is for informational purposes only and not financial advice."
```

---

#### Tool 6: `escalate_to_human`
```python
def escalate_to_human(
    category: str,
    summary: str,
    priority: str = "normal",
    customer_contact: str | None = None
) -> dict:
    """
    Escalate the conversation to a human agent. Creates a support ticket.
    Use when: complaint, account-specific query needing auth, transaction request,
    or customer explicitly asks for a human.

    Args:
        category: "complaint", "account_query", "transaction_request", "other"
        summary: Brief summary of the issue for the human agent
        priority: "low", "normal", "high", "urgent"
        customer_contact: Email or phone if provided

    Returns:
        { ticket_id, estimated_response_time, message_to_customer }
    """
```

**When LLM should use this:** Customer says "I want to speak to a person", complaints, transaction requests (buy/sell), account-specific queries requiring authentication.

**Escalation notification:** Creates a DynamoDB ticket, sends confirmation email to customer (via SES), and sends notification email to the support team.

---

### System Prompt

```
You are an AI customer support agent for Al Meezan Investments, Pakistan's largest
Shariah-compliant asset management company.

ROLE:
- Answer questions about Al Meezan mutual funds, Islamic finance, account services
- Use your tools to look up accurate fund data (NAV, performance, comparisons)
- Help customers understand their risk profile and suitable fund allocation
- Escalate to human agents when appropriate

RULES:
1. Always use tools for factual data (NAV, returns, fees) — never make up numbers
2. For risk profiling, gather all required info through conversation before calling the tool
3. Always include the disclaimer for investment suggestions
4. If the customer asks about account-specific info (balance, transactions), escalate
5. Be professional, warm, and concise. Use Pakistani financial context.
6. If unsure, say so honestly and offer to escalate

TOOLS AVAILABLE:
- search_knowledge_base: For FAQs, processes, regulations
- get_fund_nav: Current NAV lookup
- get_fund_performance: Fund return metrics
- compare_funds: Side-by-side fund comparison
- assess_risk_profile: Investment risk assessment (gather all inputs first)
- escalate_to_human: Create support ticket for human agent
```

---

## 4. Knowledge Base

### Layer 1: Al Meezan Fund Data (structured, refreshed daily)

Stored in DynamoDB `funds` table (not ChromaDB — this is structured data for tool lookups):

| Data | Source | Refresh |
|------|--------|---------|
| Fund NAVs (all 15+ funds) | MUFAP daily NAV page | Daily (scheduled task) |
| Fund performance (YTD, 1Y, 3Y, 5Y) | MUFAP performance table | Daily |
| Fund metadata (category, fee, rating, benchmark) | Al Meezan website | Monthly |

**Seed script** will download and parse from MUFAP.

### Layer 2: Al Meezan Knowledge Documents (unstructured, for RAG)

Stored in ChromaDB via embeddings:

| Document | Source | Category |
|----------|--------|----------|
| Fund Manager Report (monthly PDF) | almeezangroup.com/assets/uploads/ | `fund_docs` |
| Fund prospectuses / constitutive docs | almeezangroup.com downloads section | `fund_docs` |
| FAQ content (account opening, digital account, Shariah) | almeezangroup.com/frequently-asked-questions | `faq` |
| Investor guides (KYC, redemption, switching) | Al Meezan website | `process` |
| SECP Mutual Fund Regulations 2025 | secp.gov.pk | `secp` |
| SECP Investor suitability guidelines | secp.gov.pk | `secp` |
| MUFAP investor education materials | mufap.com.pk | `education` |

**Seed script** (`knowledge_base/scripts/seed.py`):
- Downloads PDFs from verified URLs
- Scrapes FAQ content from Al Meezan website
- Generates metadata.json with checksums

### Layer 3: Admin-Uploaded Documents

- Admins upload additional docs via admin panel (internal SOPs, new product guides)
- Processed through same pipeline: S3 → parse → chunk → embed → ChromaDB

### ChromaDB Collection

Single collection: `almeezan_knowledge`

Chunk metadata:
```json
{
  "doc_id": "uuid",
  "doc_title": "FMR February 2026",
  "category": "fund_docs",
  "source_url": "https://almeezangroup.com/assets/uploads/2026/02/FMR-February-2026.pdf",
  "page_number": 5,
  "chunk_index": 12,
  "uploaded_by": "system"
}
```

### Chunking Strategy
- **Chunk size:** 512 tokens (~380 words)
- **Overlap:** 64 tokens
- **Splitter:** Recursive character splitter (paragraph → sentence → word)
- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` → 384 dimensions

---

## 5. Data Models (DynamoDB Schemas)

> Table names follow pattern: `acc-{environment}-{table}`
> Example: `acc-staging-conversations`, `acc-prod-tickets`

### Table: `acc-{env}-funds`

Structured fund data for tool calls (NOT for RAG — queried directly).

| Field | Type | Description |
|-------|------|-------------|
| `fundId` | String (PK) | Ticker symbol, e.g. `MIF`, `MIIF`, `MCF` |
| `fullName` | String | "Meezan Islamic Fund" |
| `category` | String | `equity`, `income`, `money_market`, `balanced`, `commodity`, `etf` |
| `nav` | Number | Current NAV (PKR) |
| `navDate` | String | ISO 8601 date of NAV |
| `returns` | Map | `{ "1d": 0.1, "1m": 1.2, "ytd": 18.5, "1y": 22.3, "3y": 45.7, "5y": 80.1 }` |
| `managementFeePct` | Number | Annual management fee % |
| `frontEndLoadPct` | Number | Front-end load % |
| `benchmark` | String | Benchmark index name |
| `riskLevel` | String | `low`, `medium`, `high` |
| `fundRating` | String | e.g. `AA(f)` from PACRA |
| `shariahCompliant` | Boolean | Always `true` for Al Meezan |
| `minInvestmentPkr` | Number | Minimum initial investment |
| `lastUpdated` | String | ISO 8601 UTC |

---

### Table: `acc-{env}-conversations`

| Field | Type | Description |
|-------|------|-------------|
| `conversationId` | String (PK) | UUID v4 |
| `sessionId` | String | WebSocket session ID |
| `customerName` | String | Optional (if provided) |
| `customerContact` | String | Optional email/phone |
| `status` | String | `active`, `resolved`, `escalated` |
| `toolsUsed` | List | `["get_fund_nav", "assess_risk_profile"]` |
| `messageCount` | Number | Running count |
| `createdAt` | String | ISO 8601 UTC |
| `lastMessageAt` | String | ISO 8601 UTC |
| `resolvedAt` | String | ISO 8601 UTC (if resolved) |

---

### Table: `acc-{env}-messages`

| Field | Type | Description |
|-------|------|-------------|
| `conversationId` | String (PK) | Parent conversation |
| `messageId` | String (SK) | `{timestamp_ms}#{uuid_short}` — chronological sort |
| `role` | String | `customer`, `assistant`, `tool_call`, `tool_result` |
| `content` | String | Message text or tool result JSON |
| `toolName` | String | (if role=tool_call) which tool was invoked |
| `toolArgs` | Map | (if role=tool_call) arguments passed |
| `sources` | List | (if role=assistant) list of `{doc_title, score, chunk_text}` |
| `latencyMs` | Number | Response generation time |
| `tokenCount` | Number | Tokens used |
| `createdAt` | String | ISO 8601 UTC |

---

### Table: `acc-{env}-tickets`

Created when agent calls `escalate_to_human`.

| Field | Type | Description |
|-------|------|-------------|
| `ticketId` | String (PK) | UUID v4 |
| `conversationId` | String | Link to conversation |
| `category` | String | `complaint`, `account_query`, `transaction_request`, `other` |
| `summary` | String | AI-generated summary of the issue |
| `priority` | String | `low`, `normal`, `high`, `urgent` |
| `status` | String | `open` → `assigned` → `resolved` → `closed` |
| `assignedTo` | String | Agent email (when assigned) |
| `customerContact` | String | Email or phone |
| `customerName` | String | If provided |
| `resolution` | String | How it was resolved |
| `createdAt` | String | ISO 8601 UTC |
| `resolvedAt` | String | ISO 8601 UTC |

**GSI:** `StatusIndex` — HashKey: `status` — for admin dashboard ticket queue

---

### Table: `acc-{env}-documents`

Knowledge base document metadata.

| Field | Type | Description |
|-------|------|-------------|
| `documentId` | String (PK) | UUID v4 |
| `title` | String | Human-readable title |
| `s3Key` | String | `documents/{documentId}/{filename}` |
| `fileType` | String | `pdf`, `docx`, `md`, `txt` |
| `fileSizeBytes` | Number | File size |
| `status` | String | `pending` → `processing` → `ready` → `failed` |
| `failureReason` | String | Error message if `failed` |
| `chunkCount` | Number | Chunks in ChromaDB |
| `category` | String | `faq`, `fund_docs`, `secp`, `process`, `internal` |
| `uploadedBy` | String | userId of uploader |
| `createdAt` | String | ISO 8601 UTC |
| `processedAt` | String | ISO 8601 UTC |

---

### Table: `acc-{env}-users`

Admin panel users (not customers — customers are anonymous chat users).

| Field | Type | Description |
|-------|------|-------------|
| `userId` | String (PK) | UUID v4 |
| `email` | String | Unique, GSI hash key |
| `hashedPassword` | String | bcrypt hash (cost 12) |
| `role` | String | `admin`, `agent` |
| `isActive` | Boolean | Soft-disable |
| `fullName` | String | Display name |
| `createdAt` | String | ISO 8601 UTC |

**GSI:** `EmailIndex` — for login lookup

---

### Table: `acc-{env}-response-ratings`

Admin/agent quality ratings on AI responses (feeds MLOps quality metrics).

| Field | Type | Description |
|-------|------|-------------|
| `ratingId` | String (PK) | UUID v4 |
| `messageId` | String | Which AI message was rated |
| `conversationId` | String | Parent conversation |
| `rating` | String | `good`, `bad`, `incorrect` |
| `correctedAnswer` | String | What the correct answer should have been (optional) |
| `ratedBy` | String | userId of admin/agent |
| `createdAt` | String | ISO 8601 UTC |

---

## 6. API Contract (All Endpoints)

**Base URL:** `http://localhost:8000/api/v1`

---

### Chat (WebSocket)

#### `WS /api/v1/chat/ws`
```json
// Client → Server (customer message)
{ "type": "message", "content": "What is the NAV of MIF?" }

// Server → Client (agent is thinking)
{ "type": "status", "content": "thinking" }

// Server → Client (tool call in progress — shown as "Looking up fund data...")
{ "type": "tool_call", "tool": "get_fund_nav", "status": "calling" }

// Server → Client (streamed response chunks)
{ "type": "chunk", "content": "The current NAV of " }
{ "type": "chunk", "content": "Meezan Islamic Fund is " }
{ "type": "chunk", "content": "PKR 45.23 as of April 25, 2026." }

// Server → Client (sources, sent after response completes)
{ "type": "sources", "sources": [ { "title": "MUFAP NAV Data", "score": 0.95 } ] }

// Server → Client (done)
{ "type": "done", "latencyMs": 3200, "tokensUsed": 412 }
```

---

### Conversations (REST — for admin panel)

#### `GET /api/v1/conversations/` *(requires admin auth)*
```json
// Query: ?status=active&limit=20&cursor=xxx
{
  "items": [
    {
      "conversationId": "uuid",
      "status": "active",
      "messageCount": 8,
      "toolsUsed": ["get_fund_nav", "assess_risk_profile"],
      "createdAt": "2026-04-26T10:00:00Z",
      "lastMessageAt": "2026-04-26T10:05:00Z"
    }
  ],
  "nextCursor": "base64key"
}
```

#### `GET /api/v1/conversations/{conversationId}/messages` *(requires admin auth)*

---

### Tickets (REST — for admin panel)

#### `GET /api/v1/tickets/` *(requires admin auth)*
```json
// Query: ?status=open&priority=high&limit=20
```

#### `PATCH /api/v1/tickets/{ticketId}` *(requires admin auth)*
```json
// Request — assign or resolve
{ "status": "assigned", "assignedTo": "agent@almeezan.com" }
// or
{ "status": "resolved", "resolution": "Customer was guided through KYC process" }
```

---

### Documents (REST — for admin panel KB management)

#### `POST /api/v1/documents/upload` *(requires admin auth, multipart)*
#### `GET /api/v1/documents/` *(requires admin auth)*
#### `GET /api/v1/documents/{documentId}/chunks` *(requires admin auth)*
#### `DELETE /api/v1/documents/{documentId}` *(requires admin auth)*
#### `POST /api/v1/documents/{documentId}/reindex` *(requires admin auth)*

---

### Funds (REST — internal, used by tools)

#### `GET /api/v1/funds/` — List all funds with latest NAV
#### `GET /api/v1/funds/{fundId}` — Single fund detail
#### `GET /api/v1/funds/{fundId}/performance` — Performance metrics

---

### Quality Ratings (REST — admin rates AI responses)

#### `POST /api/v1/ratings/` *(requires admin auth)*
```json
{ "messageId": "xxx", "conversationId": "yyy", "rating": "good" }
```

#### `GET /api/v1/ratings/stats` *(requires admin auth)*
```json
// Returns aggregated quality metrics
{ "total": 500, "good": 420, "bad": 50, "incorrect": 30, "accuracy_pct": 84.0 }
```

---

### Auth

#### `POST /api/v1/auth/login`
#### `GET /api/v1/auth/me` *(requires auth)*

---

### Health

#### `GET /health`
```json
{ "status": "ok", "version": "1.0.0", "environment": "staging" }
```

---

## 7. Chat Widget (Embeddable JS)

A lightweight JavaScript widget that any website embeds via a single `<script>` tag.

### Integration Code (for client website)
```html
<!-- Al Meezan AI Support Widget -->
<script src="https://your-cdn-or-alb/static/widget.js"></script>
<script>
  AlMeezanChat.init({
    apiUrl: "wss://your-alb-dns/api/v1/chat/ws",
    theme: "dark",       // "light" or "dark"
    position: "bottom-right",
    greeting: "Assalam o Alaikum! How can I help you with your investment queries today?"
  });
</script>
```

### Widget Behaviour
- **Collapsed state:** Floating button (bottom-right) with Al Meezan brand color (#006B3F)
- **Expanded state:** Chat window (400×550px) with:
  - Header: "Al Meezan Support" + minimize button
  - Message area: scrollable, auto-scroll to bottom
  - Customer messages: right-aligned, green bubble
  - Agent messages: left-aligned, white bubble, with markdown rendering
  - Tool call indicators: "🔍 Looking up fund data..." shown while tools execute
  - Source citations: collapsible section after agent response
  - Input area: text input + send button
- **Connection:** WebSocket (reconnects automatically on disconnect)
- **Session persistence:** `conversationId` stored in `sessionStorage` (cleared on tab close)
- **No login required:** Customers are anonymous

### Files
```
widget/
├── widget.js           ← Self-contained IIFE (no dependencies)
├── widget.css          ← Inline styles (injected by JS, no external CSS)
└── widget.html         ← Local dev test page
```

---

## 8. Admin Panel (Web UI)

Server-rendered HTML pages served by FastAPI + Jinja2 templates. Simple, no React/Next.js.

### Pages

| Route | Description |
|-------|------------|
| `/admin/login` | Email + password login |
| `/admin/dashboard` | Overview: active conversations, open tickets, quality metrics |
| `/admin/conversations` | List all conversations, click to view full transcript |
| `/admin/conversations/{id}` | Full conversation transcript with tool calls visible |
| `/admin/tickets` | Ticket queue: filter by status/priority, assign, resolve |
| `/admin/knowledge-base` | List documents, upload new, delete, reindex |
| `/admin/knowledge-base/{id}/chunks` | Preview indexed chunks for a document |
| `/admin/quality` | Response quality dashboard: rating stats, trends |
| `/admin/funds` | View fund data, trigger NAV refresh |

### Admin Access Model

| Action | Admin | Agent |
|--------|-------|-------|
| View dashboard | ✅ | ✅ |
| View conversations | ✅ | ✅ |
| Rate AI responses (👍/👎) | ✅ | ✅ |
| Manage tickets (assign/resolve) | ✅ | ✅ |
| Upload/delete KB documents | ✅ | ❌ |
| Manage users | ✅ | ❌ |
| Trigger NAV refresh | ✅ | ❌ |


### Design
- Simple, clean HTML/CSS — no heavy framework
- Responsive (works on desktop and tablet)
- DataTables or plain HTML tables with server-side pagination
- Charts: lightweight (Chart.js) for quality dashboard

---

## 9. LLMOps & Quality Pipeline

> To present a strong "MLOps / LLMOps" story, we avoid traditional model training and instead implement an **Agent Evaluation Pipeline** (the modern standard for LLM systems).

### LLMOps: Automated Prompt & Tool Evaluation

Before deploying prompt changes to production, we must guarantee that the agent still calls the correct tools.
1. **Golden Dataset**: A JSON file (`tests/eval/golden_dataset.json`) containing 50-100 test queries and their expected tool calls. (e.g., `{"query": "What's the NAV?", "expected_tool": "get_fund_nav"}`).
2. **Evaluation Engine**: A script (`backend/scripts/evaluate_agent.py`) that runs the agent against the golden dataset.
3. **Metrics Tracked**:
   - **Tool Calling Accuracy**: % of times the correct tool was selected.
   - **RAG Retrieval Score**: % of times the correct document was found in ChromaDB.
   - **Latency**: P50 / P99 response times.
4. **CI/CD Integration**: The evaluation engine runs automatically on GitHub PRs. If tool accuracy drops below 90%, the PR is blocked.

### Quality Feedback Loop (Production)

```
Customer asks question
        ↓
AI responds (logged in DynamoDB)
        ↓
Admin reviews conversation in admin panel
        ↓
Admin rates response: 👍 good / 👎 bad / ❌ incorrect
        ↓
Rating stored in `response-ratings` table
        ↓
Admin dashboard shows quality trends:
  - accuracy_rate = good / (good + bad + incorrect)
  - avg_response_time_ms
  - tool_usage_distribution
  - escalation_rate
        ↓
Team adjusts prompts/config and runs through the LLMOps Evaluation Pipeline
```

### KB Data Pipeline

```
Admin uploads new document (via admin panel)
        ↓
S3 upload → DynamoDB status=pending
        ↓
Background task:
  1. Download from S3
  2. Parse (PDF/DOCX/MD/TXT)
  3. Chunk (512 tokens, 64 overlap)
  4. Embed (sentence-transformers)
  5. Upsert to ChromaDB
  6. Update DynamoDB status=ready
        ↓
Validation: run 5 test queries against new collection, compare scores
```

---

## 10. Repository Structure

```
Project/                              ← monorepo root
│
├── .github/
│   └── workflows/
│       ├── ci.yml                    ← lint + unit tests on all pushes
│       ├── staging.yml               ← deploy to ECS staging
│       ├── prod.yml                  ← deploy to ECS prod (approval gate)
│       └── terraform.yml             ← tf plan/apply
│
├── infrastructure/
│   ├── docker/
│   │   ├── Dockerfile.api            ← multi-stage, Python 3.11-slim
│   │   └── Dockerfile.widget         ← nginx alpine, serves static widget files
│   └── terraform/
│       ├── modules/
│       │   ├── vpc/                  ← VPC, subnets, NAT, security groups
│       │   ├── ecs/                  ← Fargate cluster, task defs, ALB
│       │   ├── dynamodb/             ← All tables with GSIs
│       │   ├── s3/                   ← Document bucket
│       │   └── iam/                  ← Task roles, OIDC deploy role
│       └── environments/
│           ├── staging/
│           │   ├── main.tf           ← Module calls with staging vars
│           │   ├── terraform.tfvars  ← Staging-specific values
│           │   └── backend.tf        ← S3 state: key = staging/terraform.tfstate
│           └── prod/
│               ├── main.tf
│               ├── terraform.tfvars
│               └── backend.tf        ← S3 state: key = prod/terraform.tfstate
│
├── backend/
│   ├── app/
│   │   ├── main.py                   ← FastAPI app factory, routers, lifespan
│   │   ├── core/
│   │   │   ├── config.py             ← pydantic-settings (all env vars)
│   │   │   ├── dynamo.py             ← DynamoDB client + helpers
│   │   │   ├── security.py           ← JWT + bcrypt
│   │   │   └── dependencies.py       ← get_current_user, require_admin
│   │   │
│   │   ├── agent/                    ← AI Agent (core differentiator)
│   │   │   ├── orchestrator.py       ← Agent loop: receive → LLM → tool call → respond
│   │   │   ├── system_prompt.py      ← System prompt template (versioned)
│   │   │   ├── tools/
│   │   │   │   ├── search_kb.py      ← search_knowledge_base tool
│   │   │   │   ├── fund_nav.py       ← get_fund_nav tool
│   │   │   │   ├── fund_perf.py      ← get_fund_performance tool
│   │   │   │   ├── compare.py        ← compare_funds tool
│   │   │   │   ├── risk_profile.py   ← assess_risk_profile tool
│   │   │   │   └── escalate.py       ← escalate_to_human tool
│   │   │   └── tool_registry.py      ← Maps tool names → functions + schemas
│   │   │
│   │   ├── routers/
│   │   │   ├── chat_ws.py            ← WebSocket endpoint for chat widget
│   │   │   ├── conversations.py      ← Admin: list/view conversations
│   │   │   ├── tickets.py            ← Admin: ticket CRUD
│   │   │   ├── documents.py          ← Admin: KB document management
│   │   │   ├── funds.py              ← Fund data endpoints (internal)
│   │   │   ├── ratings.py            ← Response quality ratings
│   │   │   └── auth.py               ← Login, me
│   │   │
│   │   ├── services/
│   │   │   ├── embedding_service.py  ← sentence-transformers (local, 384d)
│   │   │   ├── vector_service.py     ← ChromaDB CRUD + search
│   │   │   ├── llm_service.py        ← Groq client with tool calling support
│   │   │   ├── document_processor.py ← PDF/DOCX/MD → chunks
│   │   │   ├── storage_service.py    ← S3 upload/download
│   │   │   └── fund_data_service.py  ← DynamoDB fund queries for tools
│   │   │
│   │   ├── pipeline/
│   │   │   └── ingestion.py          ← S3 → parse → chunk → embed → ChromaDB
│   │   │
│   │   └── admin/                    ← Admin panel (Jinja2 templates)
│   │       ├── templates/
│   │       │   ├── base.html         ← Layout with nav
│   │       │   ├── login.html
│   │       │   ├── dashboard.html
│   │       │   ├── conversations.html
│   │       │   ├── conversation_detail.html
│   │       │   ├── tickets.html
│   │       │   ├── knowledge_base.html
│   │       │   └── quality.html
│   │       ├── static/               ← Admin CSS + JS
│   │       └── views.py              ← Admin page routes (renders templates)
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── unit/
│   │   │   ├── test_tools.py         ← Each tool function independently
│   │   │   ├── test_orchestrator.py   ← Agent loop with mocked LLM
│   │   │   ├── test_risk_profile.py   ← Risk scoring logic
│   │   │   └── test_document_processor.py
│   │   ├── integration/
│   │   │   ├── test_chat_ws.py        ← WebSocket chat flow
│   │   │   ├── test_tickets.py
│   │   │   └── test_documents.py
│   │   └── eval/
│   │       └── golden_dataset.json    ← LLMOps Evaluation Test Cases
│   │
│   ├── scripts/
│   │   └── evaluate_agent.py          ← LLMOps Tool Evaluation Engine
│   │
│   ├── pyproject.toml
│   └── requirements.txt
│
├── widget/                           ← Embeddable chat widget (static JS/CSS)
│   ├── widget.js
│   ├── widget.css
│   └── widget.html                   ← Local dev test page
│
├── knowledge_base/
│   ├── scripts/
│   │   └── seed.py                   ← Download Al Meezan + MUFAP + SECP docs
│   └── raw_docs/                     ← Downloaded PDFs (gitignored)
│
├── .pre-commit-config.yaml
├── docker-compose.yml                ← Local: api + chromadb + dynamodb-local
├── Makefile
├── .env.example
├── .gitignore
├── PROJECT_PLAN.md                   ← THIS FILE
└── README.md
```

---

## 11. Infrastructure (Terraform Guide)

> No .tf files are committed — team builds Terraform following this guide.
> Key design: **shared modules**, **separate tfvars per environment**, **S3 state with DynamoDB lock**.

### Terraform Directory Layout

```
infrastructure/terraform/
├── modules/                          ← Shared, reusable modules
│   ├── vpc/
│   │   ├── main.tf                   ← VPC, 2 public + 2 private subnets, 1 NAT GW, SGs
│   │   ├── variables.tf              ← project_name, environment, vpc_cidr, az_count
│   │   └── outputs.tf                ← vpc_id, subnet_ids, sg_ids
│   ├── ecs/
│   │   ├── main.tf                   ← Cluster, task def, service, ALB, target groups
│   │   ├── variables.tf              ← cpu, mem, desired_count, image, env_vars, subnets, sgs
│   │   └── outputs.tf                ← cluster_name, alb_dns, service_name
│   ├── dynamodb/
│   │   ├── main.tf                   ← All 7 tables with GSIs, PITR config
│   │   ├── variables.tf              ← project_name, environment, enable_pitr
│   │   └── outputs.tf                ← table_names, table_arns
│   ├── s3/
│   │   ├── main.tf                   ← Bucket, encryption, lifecycle, versioning
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── iam/
│       ├── main.tf                   ← Task exec role, task role, OIDC deploy role
│       ├── variables.tf
│       └── outputs.tf
│
└── environments/
    ├── staging/
    │   ├── backend.tf                ← S3 backend { key = "staging/terraform.tfstate" }
    │   ├── main.tf                   ← module "vpc" { source = "../../modules/vpc" ... }
    │   ├── terraform.tfvars          ← environment="staging", api_cpu=256, api_mem=512, desired_count=1
    │   └── outputs.tf
    └── prod/
        ├── backend.tf                ← S3 backend { key = "prod/terraform.tfstate" }
        ├── main.tf                   ← Same modules, different vars
        ├── terraform.tfvars          ← environment="prod", api_cpu=512, api_mem=1024, desired_count=2, enable_pitr=true
        └── outputs.tf
```

### Remote State Setup (one-off bootstrap)

```bash
# Create S3 bucket for state (run once in AWS console or CLI)
aws s3api create-bucket --bucket acc-terraform-state --region us-east-1
aws s3api put-bucket-versioning --bucket acc-terraform-state --versioning-configuration Status=Enabled

# Create DynamoDB lock table (run once)
aws dynamodb create-table \
  --table-name acc-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### backend.tf (each environment)
```hcl
terraform {
  backend "s3" {
    bucket         = "acc-terraform-state"
    key            = "staging/terraform.tfstate"   # or "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "acc-terraform-locks"
  }
}
```

### Environment Sizing

| Resource | Staging | Prod |
|----------|---------|------|
| ECS Fargate API | 0.25 vCPU, 0.5 GB, 1 task | 0.5 vCPU, 1 GB, 2 tasks |
| DynamoDB | PAY_PER_REQUEST, no PITR | PAY_PER_REQUEST, PITR on |
| S3 lifecycle | 30 days → IA | 90 days → Glacier |
| ALB | 1 (public) | 1 (public) |
| NAT Gateway | 1 AZ | 1 AZ |

---

## 12. CI/CD Pipelines (GitHub Actions)

### `ci.yml` — Every push
```yaml
Trigger: push to any branch, pull_request to staging or main
Steps:
  1. Checkout
  2. Setup Python 3.11 (cached pip)
  3. Install requirements
  4. pre-commit run --all-files (ruff, mypy, bandit, detect-secrets)
  5. pytest tests/unit/ -v --cov=app --cov-report=xml
  6. Upload coverage to Codecov
```

### `staging.yml` — Push to staging
```yaml
Trigger: push to staging branch
Steps:
  1. Reuse ci.yml
  2. Configure AWS OIDC credentials
  3. docker build + push to ECR (tag: staging-{sha})
  4. aws ecs update-service --force-new-deployment
  5. Wait for stability
  6. Run smoke tests
  7. Email notification via SES to team
```

### `prod.yml` — Push to main
```yaml
Trigger: push to main
Steps:
  1. Reuse ci.yml
  2. MANUAL APPROVAL GATE (GitHub environment: production)
  3. Configure AWS OIDC credentials
  4. docker build + push to ECR (tag: prod-{sha} + prod-latest)
  5. aws ecs update-service
  6. Health check: curl /health
  7. Email notification via SES (success/failure)
```

### `terraform.yml` — Infrastructure changes
```yaml
Trigger: push to infrastructure branch, workflow_dispatch for apply
Steps:
  1. terraform fmt --check
  2. terraform validate (staging + prod)
  3. terraform plan → comment on PR
  4. Manual apply via workflow_dispatch
```

### Branch Strategy

| Branch | Purpose | Deploy |
|--------|---------|--------|
| `feature/ACC-{ticket}` | Development | Local |
| `staging` | Integration/QA | → ECS staging |
| `main` | Production | → ECS prod (approval gate) |
| `infrastructure` | Terraform only | Plan auto, Apply manual |

---

## 13. Code Quality & Pre-commit Hooks

| Hook | Tool | What It Catches |
|------|------|----------------|
| Ruff lint | ruff | PEP8, unused imports, bad patterns |
| Ruff format | ruff | Consistent code formatting |
| Mypy | mypy | Type errors |
| Bandit | bandit | Security vulnerabilities |
| detect-secrets | Yelp detect-secrets | Leaked API keys/tokens |
| Hadolint | hadolint | Dockerfile best practices |
| Terraform fmt | terraform | HCL formatting |
| Trailing whitespace | pre-commit-hooks | Formatting noise |
| YAML/JSON check | pre-commit-hooks | Syntax errors |

---

## 14. Testing Strategy

### Unit Tests (no external deps)

| File | What to Test |
|------|-------------|
| `test_tools.py` | Each tool function: NAV lookup, fund comparison, risk scoring |
| `test_orchestrator.py` | Agent loop with mocked LLM: tool selection, multi-tool calls |
| `test_risk_profile.py` | Risk scoring algorithm: edge cases, boundary values |
| `test_document_processor.py` | PDF/DOCX/MD parsing, chunk size validation |

### Integration Tests (Docker Compose up)

| File | What to Test |
|------|-------------|
| `test_chat_ws.py` | WebSocket chat flow: connect → send → receive chunks → done |
| `test_tickets.py` | Escalation flow: create ticket, assign, resolve |
| `test_documents.py` | Upload → process → search → delete |

### Test Fixtures (conftest.py)
```python
@pytest.fixture  client           # TestClient(app) with auth
@pytest.fixture  ws_client        # WebSocket test client
@pytest.fixture  dynamo_tables    # DynamoDB Local tables (cleaned per test)
@pytest.fixture  chroma_client    # In-memory ChromaDB
@pytest.fixture  mock_groq        # Mocked Groq API (returns predictable tool calls)
@pytest.fixture  admin_user       # Pre-seeded admin + JWT
@pytest.fixture  sample_funds     # Pre-seeded fund data in DynamoDB
```

---

## 15. Environment Variables Reference

```env
# ── App ──────────────────────────────────────────────────────
ENVIRONMENT=development          # development | staging | production
SECRET_KEY=<32-byte hex>         # openssl rand -hex 32
CORS_ORIGINS=http://localhost:3000

# ── AWS ──────────────────────────────────────────────────────
AWS_REGION=us-east-1
S3_BUCKET_NAME=acc-documents-dev

# ── DynamoDB ─────────────────────────────────────────────────
DYNAMODB_ENDPOINT_URL=http://localhost:8001   # LOCAL ONLY
TABLE_PREFIX=acc-development                 # tables: {prefix}-funds, {prefix}-conversations, ...

# ── ChromaDB ─────────────────────────────────────────────────
CHROMA_HOST=chromadb
CHROMA_PORT=8000
CHROMA_COLLECTION=almeezan_knowledge

# ── LLM (Groq — free tier) ──────────────────────────────────
GROQ_API_KEY=gsk_xxx             # Free: console.groq.com
GROQ_MODEL=llama-3.1-70b-versatile

# ── Embeddings ───────────────────────────────────────────────
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# ── Email (SES — ticket + deploy notifications) ─────────────
SES_SENDER_EMAIL=support@almeezan.com  # Verified SES sender
SES_SUPPORT_TEAM_EMAIL=support-team@almeezan.com  # Internal team inbox

# ── Admin Auth ───────────────────────────────────────────────
ADMIN_EMAIL=admin@almeezan.com
ADMIN_PASSWORD=change-me-now
JWT_SECRET_KEY=<32-byte hex>
JWT_EXPIRE_MINUTES=480           # 8 hours


```

---

## 16. Local Development Setup

```bash
# 1. Clone and configure
git clone https://github.com/saademad200/banking-kms.git
cd banking-kms
cp .env.example .env
# Edit .env: set GROQ_API_KEY + ADMIN_PASSWORD at minimum

# 2. Install pre-commit hooks
pip install pre-commit && pre-commit install

# 3. Start all services
docker compose up --build
# API:            http://localhost:8000
# API Docs:       http://localhost:8000/docs
# Admin Panel:    http://localhost:8000/admin
# Chat Widget:    http://localhost:8000/static/widget.html
# DynamoDB Admin: http://localhost:8888
# ChromaDB:       http://localhost:8002


# 4. Create DynamoDB tables (local)
docker compose exec api python -m app.core.dynamo_init

# 5. Seed knowledge base (download Al Meezan + MUFAP docs)
pip install httpx beautifulsoup4
python knowledge_base/scripts/seed.py

# 6. Ingest knowledge base into ChromaDB
docker compose exec api python -m app.pipeline.ingestion --seed

# 7. Run tests
make test-unit
make test-integration
```



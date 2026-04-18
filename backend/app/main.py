"""
KMS API Entry Point
===================
FastAPI application factory.

Responsibilities (see PROJECT_PLAN.md §7 API Contract):
- Create FastAPI app with title, version, CORS middleware
- Register routers: auth, documents, chat, admin
- Lifespan events: init DynamoDB tables, load embedding model, connect ChromaDB
- Health endpoint: GET /health

Team: implement this file per the spec in PROJECT_PLAN.md
"""

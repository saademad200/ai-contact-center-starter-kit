"""
FastAPI Application Factory
============================
Mounts:
  - /api/v1          → REST API routers
  - /ws              → WebSocket chat
  - /admin           → Jinja2 admin panel
  - /health          → ALB health check
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    admin,
    auth,
    chat_ws,
    conversations,
    documents,
    llmops,
    ratings,
    tickets,
)

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting Alfalah GPT API (env=%s)", settings.environment)
    # Initialise Langfuse AFTER settings has loaded secrets from AWS Secrets Manager
    from app.agent.orchestrator import init_langfuse  # noqa: PLC0415
    init_langfuse()
    yield
    logger.info("Shutting down Alfalah GPT API")


app = FastAPI(
    title="Alfalah GPT API",
    description="AI-powered customer support for Alfalah Investments",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)
app.include_router(conversations.router, prefix=API_PREFIX)
app.include_router(documents.router, prefix=API_PREFIX)
app.include_router(ratings.router, prefix=API_PREFIX)
app.include_router(tickets.router, prefix=API_PREFIX)
app.include_router(llmops.router, prefix=API_PREFIX)
app.include_router(chat_ws.router)  # mounts at /ws/chat/{conversation_id}


# ── Health Check ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health() -> dict[str, Any]:
    return {"status": "ok", "environment": settings.environment}

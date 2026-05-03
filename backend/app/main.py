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
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.routers import auth, chat_ws, conversations, documents, ratings, tickets, llmops
from app.admin import views as admin_views

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Alfalah GPT API (env=%s)", settings.environment)
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
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.jwt_secret_key,
    session_cookie="alf_admin_session",
    max_age=settings.jwt_access_token_expire_minutes * 60,
)

# ── Routers ────────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(conversations.router, prefix=API_PREFIX)
app.include_router(documents.router, prefix=API_PREFIX)
app.include_router(ratings.router, prefix=API_PREFIX)
app.include_router(tickets.router, prefix=API_PREFIX)
app.include_router(llmops.router, prefix=API_PREFIX)
app.include_router(chat_ws.router)  # mounts at /ws/chat/{conversation_id}
app.include_router(admin_views.router)  # mounts at /admin

# Static files for the admin panel CSS/JS
_admin_static = Path(__file__).parent / "admin" / "static"
app.mount("/admin/static", StaticFiles(directory=str(_admin_static)), name="admin-static")


# ── Health Check ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "environment": settings.environment}

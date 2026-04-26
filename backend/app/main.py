"""
FastAPI Application Factory
============================
See PROJECT_PLAN.md §10 for full specification.

Responsibilities:
- Create FastAPI app with lifespan events
- Mount all routers under /api/v1
- Serve admin panel at /admin
- Serve static files (widget) at /static
- Configure CORS for chat widget origins
- Health check at GET /health
"""

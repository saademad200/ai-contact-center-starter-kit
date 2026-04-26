"""
FastAPI Dependencies
=====================
See PROJECT_PLAN.md §8 for admin panel access model.

Provides:
- get_current_user(token) → UserDict (from JWT in cookie or Authorization header)
- require_admin(user) → raises 403 if role != "admin"
- require_agent_or_admin(user) → raises 403 if role not in ("admin", "agent")
"""

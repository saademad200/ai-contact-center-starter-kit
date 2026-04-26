"""
Security: JWT + Password Hashing
==================================
See PROJECT_PLAN.md §6 for auth endpoints.

Provides:
- create_access_token(user_id, role) → JWT string
- verify_token(token) → dict payload or raise
- hash_password(password) → bcrypt hash
- verify_password(plain, hashed) → bool
"""

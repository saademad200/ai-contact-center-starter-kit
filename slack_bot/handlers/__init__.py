"""
Slack Handlers
==============
Register all Bolt event handlers. See PROJECT_PLAN.md §16 for full spec.

handlers/
  ask.py        → /kms slash command + @bot mention → calls RAG API → posts Block Kit reply
  upload.py     → admin DMs a file → downloads, calls POST /documents/upload, posts status
  admin.py      → /kms-admin list|delete|reindex commands (admin Slack user only)
"""

"""
DynamoDB Local Table Bootstrap
==============================
CLI script — run inside Docker for local dev:
    docker compose exec api python -m app.core.dynamo_init

Creates all 4 tables in DynamoDB Local with correct key schemas and GSIs.
See PROJECT_PLAN.md §6 for full schema definitions.
Does nothing if tables already exist (idempotent).
"""

"""
DynamoDB Table Initializer (CLI script)
========================================
See PROJECT_PLAN.md §5 for all table schemas.

Usage: python -m app.core.dynamo_init

Creates all 7 tables in DynamoDB Local for development:
- acc-{env}-funds
- acc-{env}-conversations
- acc-{env}-messages
- acc-{env}-tickets
- acc-{env}-documents
- acc-{env}-users (+ EmailIndex GSI)
- acc-{env}-response-ratings
"""
